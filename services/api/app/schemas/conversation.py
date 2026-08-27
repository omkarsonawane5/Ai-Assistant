from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=200)

class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    archived: bool
    created_at: datetime
    updated_at: datetime

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    conversation_id: str
    role: str
    content: str
    status: str
    created_at: datetime
    updated_at: datetime

class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=12000)
