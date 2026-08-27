import asyncio
from collections.abc import AsyncIterator
from app.assistant.state import AssistantMessage
from app.providers.base import ChatModelConfig

class FakeChatModelProvider:
    def __init__(self, config: ChatModelConfig) -> None:
        self.config = config

    async def generate(self, messages: list[AssistantMessage]) -> str:
        chunks = [chunk async for chunk in self.stream(messages)]
        return "".join(chunks)

    async def stream(self, messages: list[AssistantMessage]) -> AsyncIterator[str]:
        latest = next((m.content for m in reversed(messages) if m.role == "user"), "")
        response = f"I received your message: {latest}"
        for token in response.split(" "):
            await asyncio.sleep(0)
            yield token + " "
