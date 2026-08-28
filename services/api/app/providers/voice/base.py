from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class TranscriptChunk:
    text: str
    is_final: bool = False


@dataclass(frozen=True)
class AudioChunk:
    data: bytes
    mime_type: str


class SpeechToTextProvider(Protocol):
    async def transcribe(self, audio: bytes, mime_type: str) -> AsyncIterator[TranscriptChunk]: ...


class TextToSpeechProvider(Protocol):
    async def synthesize(self, text: str) -> AsyncIterator[AudioChunk]: ...


class VoiceProviderUnavailable(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)
