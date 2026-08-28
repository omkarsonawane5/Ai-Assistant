import asyncio
import base64
import binascii
import json
from uuid import uuid4
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import TypeAdapter, ValidationError
from app.assistant.context import ContextBuilder
from app.assistant.orchestrator import AssistantOrchestrator
from app.config.settings import Settings, get_settings
from app.db.repositories.conversations import ConversationRepository
from app.db.repositories.users import UserRepository
from app.db.session import AsyncSessionLocal
from app.providers.chat.factory import create_chat_provider
from app.providers.voice.base import VoiceProviderUnavailable
from app.providers.voice.factory import create_stt_provider, create_tts_provider
from app.realtime.session_manager import VoiceSession, VoiceSessionManager
from app.schemas.realtime import AudioInputEvent, ClientEvent, HeartbeatEvent, InterruptEvent, SessionEndEvent, SessionErrorEvent, SessionReadyEvent, SessionStartEvent, TranscriptEvent, ResponseStartEvent, ResponseTextEvent, ResponseAudioEvent, ResponseEndEvent
from app.security.auth import decode_access_token

router = APIRouter(tags=["realtime"])
event_adapter = TypeAdapter(ClientEvent)


def _manager() -> VoiceSessionManager:
    from app.main import app
    return app.state.voice_sessions


async def _send(websocket: WebSocket, event) -> None:
    await websocket.send_json(event.model_dump())


async def _error(websocket: WebSocket, session_id: str, code: str, message: str, turn_id: str | None = None) -> None:
    await _send(websocket, SessionErrorEvent(event_id=str(uuid4()), session_id=session_id, turn_id=turn_id, code=code, message=message))


async def _authenticated_user_id(websocket: WebSocket, settings: Settings) -> str | None:
    # Browser WebSocket APIs cannot attach Authorization. The token is supplied as a bearer subprotocol.
    offered = websocket.headers.get("sec-websocket-protocol", "").split(",")
    token = next((value.strip()[7:] for value in offered if value.strip().startswith("bearer.")), None)
    user_id = decode_access_token(token, settings) if token else None
    if not user_id:
        return None
    async with AsyncSessionLocal() as db:
        user = await UserRepository(db).get_by_id(user_id)
    return user_id if user and user.is_active else None


@router.websocket("/realtime/sessions/{session_id}")
async def realtime_session(websocket: WebSocket, session_id: str) -> None:
    settings = get_settings()
    user_id = await _authenticated_user_id(websocket, settings)
    if not user_id:
        await websocket.close(code=4401)
        return
    await websocket.accept()
    connection_id = str(uuid4())
    session: VoiceSession | None = None
    try:
        while True:
            raw = await websocket.receive_text()
            if len(raw.encode()) > settings.realtime_max_event_bytes:
                await _error(websocket, session_id, "invalid_event", "Realtime event is too large")
                continue
            try:
                event = event_adapter.validate_json(raw)
            except (ValidationError, json.JSONDecodeError):
                await _error(websocket, session_id, "invalid_event", "Realtime event is invalid")
                continue
            if session and event.event_id in session.seen_event_ids:
                continue
            if session and not await _manager().touch(session, connection_id):
                await _error(websocket, session_id, "session_expired", "Session has expired")
                await websocket.close(code=4408)
                return
            if session:
                session.seen_event_ids.add(event.event_id)
            if isinstance(event, SessionStartEvent):
                async with AsyncSessionLocal() as db:
                    conversation = await ConversationRepository(db).get_for_user(event.conversation_id, user_id)
                if conversation is None:
                    await _error(websocket, session_id, "conversation_not_found", "Conversation not found")
                    continue
                session = await _manager().start_or_resume(session_id, user_id, event.conversation_id, event.resume, connection_id)
                if not session:
                    await _error(websocket, session_id, "session_forbidden", "Session cannot be resumed or is already connected")
                    continue
                session.seen_event_ids.add(event.event_id)
                await _send(websocket, SessionReadyEvent(event_id=str(uuid4()), session_id=session_id, conversation_id=event.conversation_id))
            elif session is None:
                await _error(websocket, session_id, "session_not_started", "Send session_start first")
            elif isinstance(event, HeartbeatEvent):
                await _send(websocket, SessionReadyEvent(event_id=str(uuid4()), session_id=session_id, conversation_id=session.conversation_id))
            elif isinstance(event, InterruptEvent):
                await _manager().interrupt(session, event.turn_id)
                await _send(websocket, ResponseEndEvent(event_id=str(uuid4()), session_id=session_id, turn_id=event.turn_id, status="interrupted"))
            elif isinstance(event, SessionEndEvent):
                await _manager().end(session)
                session = None
                await websocket.close(code=1000)
                return
            elif isinstance(event, AudioInputEvent):
                await _handle_audio(websocket, session, event, settings)
    except WebSocketDisconnect:
        pass
    finally:
        if session:
            await _manager().disconnect(session, connection_id)


async def _handle_audio(websocket: WebSocket, session: VoiceSession, event: AudioInputEvent, settings: Settings) -> None:
    previous = session.sequences.get(event.turn_id, -1)
    if event.sequence <= previous:
        await _error(websocket, session.session_id, "invalid_audio", "Audio sequence must increase", event.turn_id)
        return
    try:
        audio = base64.b64decode(event.audio_base64, validate=True) if event.audio_base64 else b""
    except (binascii.Error, ValueError):
        await _error(websocket, session.session_id, "invalid_audio", "Audio payload is not valid base64", event.turn_id)
        return
    if len(audio) > settings.realtime_max_audio_chunk_bytes:
        await _error(websocket, session.session_id, "audio_too_large", "Audio chunk exceeds the configured limit", event.turn_id)
        return
    session.sequences[event.turn_id] = event.sequence
    if not _manager().append_audio(session, event.turn_id, audio, settings.realtime_max_audio_chunk_bytes * 20):
        await _error(websocket, session.session_id, "audio_too_large", "Audio turn exceeds the configured limit", event.turn_id)
        return
    if not event.is_final:
        return
    if session.active_turn_id and session.active_turn_id != event.turn_id:
        await _manager().interrupt(session, session.active_turn_id)
    session.active_turn_id = event.turn_id
    session.active_task = asyncio.create_task(_process_turn(websocket, session, _manager().take_audio(session, event.turn_id), event.mime_type, settings))


async def _process_turn(websocket: WebSocket, session: VoiceSession, audio: bytes, mime_type: str, settings: Settings) -> None:
    turn_id = session.active_turn_id
    if not turn_id:
        return
    try:
        stt = create_stt_provider(settings)
        await _send(websocket, TranscriptEvent(event_id=str(uuid4()), session_id=session.session_id, turn_id=turn_id, type="transcript_start"))
        final_text = ""
        async for transcript in stt.transcribe(audio, mime_type):
            if turn_id in session.cancelled_turns:
                return
            event_type = "transcript_final" if transcript.is_final else "transcript_delta"
            await _send(websocket, TranscriptEvent(event_id=str(uuid4()), session_id=session.session_id, turn_id=turn_id, type=event_type, text=transcript.text))
            if transcript.is_final:
                final_text = transcript.text
        if not final_text:
            return
        async with AsyncSessionLocal() as db:
            orchestrator = AssistantOrchestrator(db, create_chat_provider(settings), ContextBuilder(settings.assistant_system_prompt, settings.recent_message_limit))
            tts = None
            try:
                tts = create_tts_provider(settings)
            except VoiceProviderUnavailable:
                await _error(websocket, session.session_id, "tts_unavailable", "Text-to-speech provider is not configured", turn_id)
            started = False
            audio_sequence = 0
            async for response in orchestrator.stream_response(user_id=session.user_id, conversation_id=session.conversation_id, user_content=final_text):
                if turn_id in session.cancelled_turns:
                    return
                if response.type == "response.started":
                    started = True
                    await _send(websocket, ResponseStartEvent(event_id=str(uuid4()), session_id=session.session_id, turn_id=turn_id, message_id=response.message_id))
                elif response.type == "text.delta":
                    await _send(websocket, ResponseTextEvent(event_id=str(uuid4()), session_id=session.session_id, turn_id=turn_id, text=response.data or ""))
                    if tts:
                        async for chunk in tts.synthesize(response.data or ""):
                            await _send(websocket, ResponseAudioEvent(event_id=str(uuid4()), session_id=session.session_id, turn_id=turn_id, mime_type=chunk.mime_type, sequence=audio_sequence, audio_base64=base64.b64encode(chunk.data).decode()))
                            audio_sequence += 1
                elif response.type == "error":
                    await _error(websocket, session.session_id, "assistant_failed", response.data or "Assistant response failed", turn_id)
                    return
            if started and turn_id not in session.cancelled_turns:
                await _send(websocket, ResponseEndEvent(event_id=str(uuid4()), session_id=session.session_id, turn_id=turn_id, status="completed"))
    except VoiceProviderUnavailable as exc:
        await _error(websocket, session.session_id, exc.code, "Speech-to-text provider is not configured", turn_id)
    except asyncio.CancelledError:
        raise
    finally:
        if session.active_turn_id == turn_id:
            session.active_turn_id = None
