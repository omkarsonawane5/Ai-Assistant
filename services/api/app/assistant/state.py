from dataclasses import dataclass

@dataclass(frozen=True)
class AssistantMessage:
    role: str
    content: str
