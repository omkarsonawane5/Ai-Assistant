import asyncio
from datetime import UTC, datetime, timedelta

from app.assistant.state import AssistantMessage
from app.providers.voice.base import AudioChunk, TranscriptChunk
from app.realtime import gateway
from app.realtime.session_manager import VoiceSession
from app.schemas.streaming import StreamEvent


class FakeSocket:
    def __init__(self):
        self.events = []

    async def send_json(self, event):
        self.events.append(event)


class FakeStt:
    def __init__(self):
        self.audio = b""

    async def transcribe(self, audio, mime_type):
        self.audio = audio
        yield TranscriptChunk("hel", False)
        yield TranscriptChunk("hello", True)


class FakeTts:
    async def synthesize(self, text):
        yield AudioChunk(text.encode(), "audio/wav")


class FakeOrchestrator:
    def __init__(self, *args):
        pass

    async def stream_response(self, **kwargs):
        yield StreamEvent(type="response.started", message_id="message")
        yield StreamEvent(type="text.delta", data="answer", message_id="message")
        yield StreamEvent(type="response.completed", message_id="message")


class FakeSessionContext:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, *args):
        return None


def test_completed_turn_streams_transcript_orchestrator_text_and_tts(monkeypatch):
    async def exercise():
        stt = FakeStt()
        monkeypatch.setattr(gateway, "create_stt_provider", lambda settings: stt)
        monkeypatch.setattr(gateway, "create_tts_provider", lambda settings: FakeTts())
        monkeypatch.setattr(gateway, "AssistantOrchestrator", FakeOrchestrator)
        monkeypatch.setattr(gateway, "AsyncSessionLocal", FakeSessionContext)
        socket = FakeSocket()
        session = VoiceSession("session", "user", "conversation", datetime.now(UTC) + timedelta(seconds=60), active_turn_id="turn")
        await gateway._process_turn(socket, session, b"firstsecond", "audio/wav", gateway.get_settings())
        assert stt.audio == b"firstsecond"
        assert [event["type"] for event in socket.events] == ["transcript_start", "transcript_delta", "transcript_final", "response_start", "response_text_delta", "response_audio", "response_end"]
    asyncio.run(exercise())
