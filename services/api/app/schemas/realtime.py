from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field

PROTOCOL_VERSION = 1


class RealtimeEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    protocol_version: Literal[1] = PROTOCOL_VERSION
    event_id: str = Field(min_length=1, max_length=100)


class SessionStartEvent(RealtimeEvent):
    type: Literal["session_start"]
    conversation_id: str = Field(min_length=1, max_length=36)
    resume: bool = False


class AudioInputEvent(RealtimeEvent):
    type: Literal["audio_input"]
    turn_id: str = Field(min_length=1, max_length=100)
    mime_type: Literal["audio/webm", "audio/ogg", "audio/wav"]
    sequence: int = Field(ge=0)
    audio_base64: str = ""
    is_final: bool = False


class InterruptEvent(RealtimeEvent):
    type: Literal["interrupt"]
    turn_id: str = Field(min_length=1, max_length=100)


class HeartbeatEvent(RealtimeEvent):
    type: Literal["heartbeat"]


class SessionEndEvent(RealtimeEvent):
    type: Literal["session_end"]


ClientEvent = Annotated[
    SessionStartEvent | AudioInputEvent | InterruptEvent | HeartbeatEvent | SessionEndEvent,
    Field(discriminator="type"),
]


class ServerEvent(RealtimeEvent):
    session_id: str
    turn_id: str | None = None


class SessionReadyEvent(ServerEvent):
    type: Literal["session_ready"] = "session_ready"
    conversation_id: str


class TranscriptEvent(ServerEvent):
    type: Literal["transcript_start", "transcript_delta", "transcript_final"]
    text: str = ""


class ResponseStartEvent(ServerEvent):
    type: Literal["response_start"] = "response_start"
    message_id: str | None = None


class ResponseTextEvent(ServerEvent):
    type: Literal["response_text_delta"] = "response_text_delta"
    text: str


class ResponseAudioEvent(ServerEvent):
    type: Literal["response_audio"] = "response_audio"
    mime_type: str
    sequence: int = Field(ge=0)
    audio_base64: str


class ResponseEndEvent(ServerEvent):
    type: Literal["response_end"] = "response_end"
    status: Literal["completed", "interrupted", "failed"]


class SessionErrorEvent(ServerEvent):
    type: Literal["session_error"] = "session_error"
    code: str
    message: str
