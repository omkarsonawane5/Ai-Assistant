from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_current_user
from app.assistant.context import ContextBuilder
from app.assistant.orchestrator import AssistantOrchestrator
from app.assistant.streaming import encode_sse
from app.config.settings import Settings, get_settings
from app.db.models import User
from app.db.repositories.conversations import ConversationRepository
from app.db.session import get_db_session
from app.providers.chat.factory import create_chat_provider
from app.schemas.conversation import ConversationCreate, ConversationResponse, MessageResponse, SendMessageRequest

router = APIRouter(prefix="/conversations", tags=["conversations"])

@router.get("", response_model=list[ConversationResponse])
async def list_conversations(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    return await ConversationRepository(session).list_for_user(user.id)

@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(payload: ConversationCreate, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    conv = await ConversationRepository(session).create(user.id, payload.title)
    await session.commit()
    return conv

@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    conv = await ConversationRepository(session).get_for_user(conversation_id, user.id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv

@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(conversation_id: str, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session)):
    repo = ConversationRepository(session)
    conv = await repo.get_for_user(conversation_id, user.id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return await repo.list_messages(conversation_id)

@router.post("/{conversation_id}/messages/stream")
async def stream_message(conversation_id: str, payload: SendMessageRequest, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db_session), settings: Settings = Depends(get_settings)):
    repo = ConversationRepository(session)
    conv = await repo.get_for_user(conversation_id, user.id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    provider = create_chat_provider(settings)
    context = ContextBuilder(settings.assistant_system_prompt, settings.recent_message_limit)
    orchestrator = AssistantOrchestrator(session, provider, context)
    async def events():
        async for event in orchestrator.stream_response(user_id=user.id, conversation_id=conversation_id, user_content=payload.content):
            yield encode_sse(event)
    return StreamingResponse(events(), media_type="text/event-stream")
