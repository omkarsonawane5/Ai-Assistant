from app.assistant.state import AssistantMessage

class ContextBuilder:
    def __init__(self, system_prompt: str, recent_message_limit: int = 20) -> None:
        self.system_prompt = system_prompt
        self.recent_message_limit = recent_message_limit

    def build(self, recent_messages: list[AssistantMessage], current_user_message: str) -> list[AssistantMessage]:
        trimmed = recent_messages[-self.recent_message_limit :]
        context = [AssistantMessage(role="system", content=self.system_prompt)]
        context.extend(message for message in trimmed if message.role in {"user", "assistant"})
        context.append(AssistantMessage(role="user", content=current_user_message))
        return context
