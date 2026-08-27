import logging
from collections.abc import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession
from app.assistant.context import ContextBuilder
from app.assistant.state import AssistantMessage
from app.db.repositories.conversations import ConversationRepository
from app.providers.base import ChatModelProvider, ProviderError
from app.schemas.streaming import StreamEvent

logger = logging.getLogger(__name__)

class AssistantOrchestrator:
    def __init__(self, session: AsyncSession, provider: ChatModelProvider, context_builder: ContextBuilder) -> None:
        self.session = session
        self.provider = provider
        self.context_builder = context_builder
        self.conversations = ConversationRepository(session)

    async def stream_response(self, *, user_id: str, conversation_id: str, user_content: str) -> AsyncIterator[StreamEvent]:
        conversation = await self.conversations.get_for_user(conversation_id, user_id)
        if conversation is None:
            yield StreamEvent(type="error", data="Conversation not found")
            return

        user_message = await self.conversations.add_message(conversation_id, "user", user_content, "completed")
        recent = await self.conversations.recent_messages(conversation_id, self.context_builder.recent_message_limit)
        context_messages = [AssistantMessage(role=m.role, content=m.content) for m in recent if m.id != user_message.id]
        model_input = self.context_builder.build(context_messages, user_content)
        assistant_message = await self.conversations.add_message(conversation_id, "assistant", "", "streaming")
        await self.session.commit()

        yield StreamEvent(type="response.started", message_id=assistant_message.id)
        parts: list[str] = []
        try:
            async for delta in self.provider.stream(model_input):
                parts.append(delta)
                yield StreamEvent(type="text.delta", data=delta, message_id=assistant_message.id)
        except ProviderError as exc:
            assistant_message.content = "".join(parts)
            assistant_message.status = "failed"
            await self.session.commit()
            logger.warning("provider_error", extra={"conversation_id": conversation_id, "retryable": exc.retryable})
            yield StreamEvent(type="error", data=str(exc), message_id=assistant_message.id)
            return
        except Exception:
            assistant_message.content = "".join(parts)
            assistant_message.status = "failed"
            await self.session.commit()
            logger.exception("assistant_stream_failed", extra={"conversation_id": conversation_id})
            yield StreamEvent(type="error", data="Assistant response failed", message_id=assistant_message.id)
            return

        assistant_message.content = "".join(parts).strip()
        assistant_message.status = "completed"
        await self.session.commit()
        yield StreamEvent(type="response.completed", message_id=assistant_message.id)
