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


class VoiceSessionManager:
    def __init__(self, ttl_seconds: int) -> None:
        self.ttl_seconds = ttl_seconds
        self._sessions: dict[str, VoiceSession] = {}
        self._lock = asyncio.Lock()

    async def start_or_resume(self, session_id: str, user_id: str, conversation_id: str, resume: bool) -> VoiceSession | None:
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
            elif resume:
                return None
            else:
                session = VoiceSession(session_id, user_id, conversation_id, now + timedelta(seconds=self.ttl_seconds))
                self._sessions[session_id] = session
            session.connected = True
            session.expires_at = now + timedelta(seconds=self.ttl_seconds)
            return session

    async def disconnect(self, session: VoiceSession) -> None:
        session.connected = False

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
