import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


@dataclass
class VoiceSession:
    session_id: str
    user_id: str
    conversation_id: str
    expires_at: datetime
    seen_event_ids: set[str] = field(default_factory=set)
    sequences: dict[str, int] = field(default_factory=dict)
    active_turn_id: str | None = None
    active_task: asyncio.Task[None] | None = None
    cancelled_turns: set[str] = field(default_factory=set)
    connected: bool = False
    connection_id: str | None = None
    audio_parts: dict[str, list[bytes]] = field(default_factory=dict)
    audio_sizes: dict[str, int] = field(default_factory=dict)


class VoiceSessionManager:
    def __init__(self, ttl_seconds: int) -> None:
        self.ttl_seconds = ttl_seconds
        self._sessions: dict[str, VoiceSession] = {}
        self._lock = asyncio.Lock()

    async def start_or_resume(self, session_id: str, user_id: str, conversation_id: str, resume: bool, connection_id: str) -> VoiceSession | None:
        await self.cleanup_expired()
        async with self._lock:
            now = datetime.now(UTC)
            session = self._sessions.get(session_id)
            if session and session.expires_at <= now:
                await self._cancel(session)
                del self._sessions[session_id]
                session = None
            if session:
                if not resume or session.user_id != user_id or session.conversation_id != conversation_id:
                    return None
                if session.connected:
                    return None
            elif resume:
                return None
            else:
                session = VoiceSession(session_id, user_id, conversation_id, now + timedelta(seconds=self.ttl_seconds))
                self._sessions[session_id] = session
            session.connected = True
            session.connection_id = connection_id
            session.expires_at = now + timedelta(seconds=self.ttl_seconds)
            return session

    async def disconnect(self, session: VoiceSession, connection_id: str) -> None:
        if session.connection_id == connection_id:
            session.connected = False
            session.connection_id = None

    async def touch(self, session: VoiceSession, connection_id: str) -> bool:
        if session.connection_id != connection_id or session.expires_at <= datetime.now(UTC):
            return False
        session.expires_at = datetime.now(UTC) + timedelta(seconds=self.ttl_seconds)
        return True

    async def cleanup_expired(self) -> None:
        async with self._lock:
            now = datetime.now(UTC)
            expired = [session for session in self._sessions.values() if not session.connected and session.expires_at <= now]
            for session in expired:
                await self._cancel(session)
                self._sessions.pop(session.session_id, None)

    def append_audio(self, session: VoiceSession, turn_id: str, audio: bytes, max_turn_bytes: int) -> bool:
        size = session.audio_sizes.get(turn_id, 0) + len(audio)
        if size > max_turn_bytes:
            return False
        session.audio_parts.setdefault(turn_id, []).append(audio)
        session.audio_sizes[turn_id] = size
        return True

    def take_audio(self, session: VoiceSession, turn_id: str) -> bytes:
        audio = b"".join(session.audio_parts.pop(turn_id, []))
        session.audio_sizes.pop(turn_id, None)
        return audio

    async def end(self, session: VoiceSession) -> None:
        async with self._lock:
            await self._cancel(session)
            self._sessions.pop(session.session_id, None)

    async def interrupt(self, session: VoiceSession, turn_id: str) -> None:
        session.cancelled_turns.add(turn_id)
        if session.active_turn_id == turn_id:
            await self._cancel(session)
            session.active_turn_id = None

    async def _cancel(self, session: VoiceSession) -> None:
        task = session.active_task
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        session.active_task = None
