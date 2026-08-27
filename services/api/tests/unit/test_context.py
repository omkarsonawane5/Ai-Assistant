from app.assistant.context import ContextBuilder
from app.assistant.state import AssistantMessage


def test_context_builder_orders_system_recent_and_current_message():
    builder = ContextBuilder("system", recent_message_limit=2)
    context = builder.build([
        AssistantMessage("user", "old"),
        AssistantMessage("assistant", "recent answer"),
        AssistantMessage("user", "recent question"),
    ], "current")
    assert [m.role for m in context] == ["system", "assistant", "user", "user"]
    assert [m.content for m in context] == ["system", "recent answer", "recent question", "current"]
