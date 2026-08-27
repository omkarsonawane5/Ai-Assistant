import pytest
from app.assistant.state import AssistantMessage
from app.providers.base import ChatModelConfig
from app.providers.chat.fake import FakeChatModelProvider

@pytest.mark.asyncio
async def test_fake_provider_streams_text():
    provider = FakeChatModelProvider(ChatModelConfig(provider="fake", model="fake-local"))
    chunks = [chunk async for chunk in provider.stream([AssistantMessage("user", "hello")])]
    assert "hello" in "".join(chunks)
