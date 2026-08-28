import base64
from pydantic import TypeAdapter, ValidationError
import pytest
from app.schemas.realtime import ClientEvent


def test_audio_event_is_validated_by_discriminator():
    event = TypeAdapter(ClientEvent).validate_python({"protocol_version": 1, "event_id": "event", "type": "audio_input", "turn_id": "turn", "mime_type": "audio/webm", "sequence": 0, "audio_base64": base64.b64encode(b"audio").decode(), "is_final": True})
    assert event.type == "audio_input"


def test_unknown_or_invalid_protocol_event_is_rejected():
    with pytest.raises(ValidationError):
        TypeAdapter(ClientEvent).validate_python({"protocol_version": 2, "event_id": "event", "type": "audio_input"})
