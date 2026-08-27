from fastapi import HTTPException, status
from app.db.models import Conversation, User

def ensure_conversation_owner(conversation: Conversation | None, user: User) -> Conversation:
    if conversation is None or conversation.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversation
