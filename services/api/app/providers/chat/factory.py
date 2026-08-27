from app.config.settings import Settings
from app.providers.base import ChatModelConfig, ChatModelProvider, ProviderError
from app.providers.chat.fake import FakeChatModelProvider
from app.providers.chat.openai import OpenAIChatModelProvider

def create_chat_provider(settings: Settings) -> ChatModelProvider:
    config = ChatModelConfig(provider=settings.ai_provider, model=settings.ai_model, api_key=settings.ai_api_key)
    match settings.ai_provider:
        case "fake":
            return FakeChatModelProvider(config)
        case "openai":
            return OpenAIChatModelProvider(config)
        case other:
            raise ProviderError(f"Unsupported AI_PROVIDER: {other}")
