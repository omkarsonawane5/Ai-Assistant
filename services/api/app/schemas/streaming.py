from typing import Literal
from pydantic import BaseModel

class StreamEvent(BaseModel):
    type: Literal["response.started", "text.delta", "response.completed", "error"]
    data: str | None = None
    message_id: str | None = None
