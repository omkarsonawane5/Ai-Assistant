import asyncio
from app.realtime.session_manager import VoiceSessionManager


def test_session_resume_requires_same_user_and_conversation():
    async def exercise():
        manager = VoiceSessionManager(60)
        session = await manager.start_or_resume("session", "user-a", "conversation-a", False)
        assert session is not None
        assert await manager.start_or_resume("session", "user-b", "conversation-a", True) is None
        assert await manager.start_or_resume("session", "user-a", "conversation-b", True) is None
        assert await manager.start_or_resume("session", "user-a", "conversation-a", True) is session
    asyncio.run(exercise())


def test_interrupt_cancels_active_turn():
    async def exercise():
        manager = VoiceSessionManager(60)
        session = await manager.start_or_resume("session", "user", "conversation", False)
        assert session is not None
        session.active_turn_id = "turn"
        await manager.interrupt(session, "turn")
        assert "turn" in session.cancelled_turns
        assert session.active_turn_id is None
    asyncio.run(exercise())
