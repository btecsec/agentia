"""Fakes for offline tests: no key, no network, same answer every time."""

import itertools

from langchain_core.language_models.fake_chat_models import (
    GenericFakeChatModel)
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda


class FakeModel(GenericFakeChatModel):
    """A chat model that plays its answers in order.

    An answer is a text, or an AIMessage carrying tool_calls.
    `structured` holds the objects with_structured_output returns.
    """

    structured: list = []
    seen: list = []

    def bind_tools(self, tools, **kwargs):
        return self

    def with_structured_output(self, schema, **kwargs):
        def answer(messages):
            self.seen.append(messages)
            return self.structured.pop(0)
        return RunnableLambda(answer)

    def _generate(self, messages, *args, **kwargs):
        self.seen.append(messages)
        return super()._generate(messages, *args, **kwargs)


def fake_model(*answers, structured=()):
    messages = [a if isinstance(a, AIMessage) else AIMessage(a)
                for a in answers]
    return FakeModel(messages=iter(messages),
                     structured=list(structured), seen=[])


def looping_model(text):
    """Same answer forever: for agents that run in parallel."""
    return FakeModel(messages=itertools.cycle([AIMessage(text)]),
                     seen=[])


def tool_call(name, **args):
    return AIMessage("", tool_calls=[
        {"name": name, "args": args, "id": f"call-{name}"}])
