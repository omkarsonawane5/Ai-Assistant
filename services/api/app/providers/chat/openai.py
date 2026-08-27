from collections.abc import AsyncIterator
from app.assistant.state import AssistantMessage
from app.providers.base import ChatModelConfig, ProviderError

class OpenAIChatModelProvider:
    def __init__(self, config: ChatModelConfig) -> None:
        self.config = config
        if not config.api_key:
            raise ProviderError("AI_API_KEY is required for the OpenAI provider")

    async def generate(self, messages: list[AssistantMessage]) -> str:
        chunks = [chunk async for chunk in self.stream(messages)]
        return "".join(chunks)

    async def stream(self, messages: list[AssistantMessage]) -> AsyncIterator[str]:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise ProviderError("Install the openai package to use AI_PROVIDER=openai") from exc
        client = AsyncOpenAI(api_key=self.config.api_key)
        stream = await client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            stream=True,
        )
        async for event in stream:
            delta = event.choices[0].delta.content
            if delta:
                yield delta
