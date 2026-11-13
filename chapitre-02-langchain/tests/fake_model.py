"""A fake LangChain chat model that replays scripted messages.

`GenericFakeChatModel` replays a list of messages; it only lacks
`bind_tools`, which `create_agent` calls to declare the tools to the
model. Here we do not care: answers are written in advance.
"""

from langchain_core.language_models.fake_chat_models import (
    GenericFakeChatModel,
)
from langchain_core.messages import AIMessage


class FakeModel(GenericFakeChatModel):
    def bind_tools(self, tools, **_):
        return self


def model_that_says(*messages):
    return FakeModel(messages=iter(messages))


def tool_call(name, arguments, call_id="a1"):
    """A model message asking to run a tool."""
    return AIMessage(
        content="",
        tool_calls=[{"name": name, "args": arguments, "id": call_id}],
    )


def answer(text):
    return AIMessage(content=text)
