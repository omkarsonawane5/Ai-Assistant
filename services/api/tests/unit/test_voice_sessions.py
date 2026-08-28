import asyncio
from app.realtime.session_manager import VoiceSessionManager


def test_session_resume_requires_same_user_and_conversation():
    async def exercise():
        manager = VoiceSessionManager(60)
        session = await manager.start_or_resume("session", "user-a", "conversation-a", False, "connection-a")
        assert session is not None
        assert await manager.start_or_resume("session", "user-b", "conversation-a", True, "connection-b") is None
        assert await manager.start_or_resume("session", "user-a", "conversation-b", True, "connection-b") is None
        assert await manager.start_or_resume("session", "user-a", "conversation-a", True, "connection-b") is None
        await manager.disconnect(session, "connection-a")
        assert await manager.start_or_resume("session", "user-a", "conversation-a", True, "connection-b") is session
    asyncio.run(exercise())


def test_interrupt_cancels_active_turn():
    async def exercise():
        manager = VoiceSessionManager(60)
        session = await manager.start_or_resume("session", "user", "conversation", False, "connection")
        assert session is not None
        session.active_turn_id = "turn"
        await manager.interrupt(session, "turn")
        assert "turn" in session.cancelled_turns
        assert session.active_turn_id is None
    asyncio.run(exercise())


def test_audio_chunks_are_retained_until_the_turn_is_finalized():
    async def exercise():
        manager = VoiceSessionManager(60)
        session = await manager.start_or_resume("session", "user", "conversation", False, "connection")
        assert session is not None
        assert manager.append_audio(session, "turn", b"first", 20)
        assert manager.append_audio(session, "turn", b"second", 20)
        assert manager.take_audio(session, "turn") == b"firstsecond"
    asyncio.run(exercise())
