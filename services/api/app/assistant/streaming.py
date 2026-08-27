import json
from app.schemas.streaming import StreamEvent

def encode_sse(event: StreamEvent) -> str:
    return f"event: {event.type}\ndata: {json.dumps(event.model_dump())}\n\n"
