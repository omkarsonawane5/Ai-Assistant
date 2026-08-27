from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol
from app.assistant.state import AssistantMessage

@dataclass(frozen=True)
class ChatModelConfig:
    provider: str
    model: str
    api_key: str | None = None

class ProviderError(Exception):
    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable

class ChatModelProvider(Protocol):
    config: ChatModelConfig
    async def generate(self, messages: list[AssistantMessage]) -> str: ...
    async def stream(self, messages: list[AssistantMessage]) -> AsyncIterator[str]: ...
