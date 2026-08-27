from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Conversation, Message

class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_user(self, user_id: str) -> list[Conversation]:
        result = await self.session.scalars(
            select(Conversation).where(Conversation.user_id == user_id, Conversation.archived.is_(False)).order_by(Conversation.updated_at.desc())
        )
        return list(result)

    async def create(self, user_id: str, title: str | None = None) -> Conversation:
        conversation = Conversation(user_id=user_id, title=title or "New conversation")
        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def get_for_user(self, conversation_id: str, user_id: str) -> Conversation | None:
        return await self.session.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id))

    async def list_messages(self, conversation_id: str, limit: int | None = None) -> list[Message]:
        stmt = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())
        if limit:
            stmt = stmt.limit(limit)
        return list(await self.session.scalars(stmt))

    async def recent_messages(self, conversation_id: str, limit: int) -> list[Message]:
        stmt = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.desc()).limit(limit)
        messages = list(await self.session.scalars(stmt))
        return list(reversed(messages))

    async def add_message(self, conversation_id: str, role: str, content: str, status: str = "completed") -> Message:
        message = Message(conversation_id=conversation_id, role=role, content=content, status=status)
        self.session.add(message)
        await self.session.flush()
        return message
