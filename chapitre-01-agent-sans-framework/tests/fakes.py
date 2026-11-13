"""Test doubles: they imitate the objects OpenRouter returns.

We do not test the model (it is not deterministic). We test OUR loop,
by replaying answers written by hand.
"""

import json


class Function:
    """The `function` part of a tool call.

    `arguments` is a JSON STRING, not a dict. That is the real API
    behaviour, and the number one trap when coming from Anthropic's dialect.
    """

    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments if isinstance(arguments, str) else json.dumps(arguments)


class ToolCall:
    type = "function"

    def __init__(self, id, name, arguments=None):  # noqa: A002 - API naming
        self.id = id
        self.function = Function(name, arguments or {})


class Message:
    role = "assistant"

    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls

    def model_dump(self, exclude_none=False):
        data = {"role": self.role, "content": self.content}
        if self.tool_calls:
            data["tool_calls"] = [
                {
                    "id": c.id,
                    "type": "function",
                    "function": {"name": c.function.name, "arguments": c.function.arguments},
                }
                for c in self.tool_calls
            ]
        return {k: v for k, v in data.items() if v is not None} if exclude_none else data


class Completion:
    def __init__(self, message):
        self.choices = [type("Choice", (), {"message": message})()]


class FakeClient:
    """Replays a script of messages and records what it was sent."""

    def __init__(self, script):
        self.script = list(script)
        self.requests = []
        self.chat = type("Chat", (), {"completions": self})()

    def create(self, **kwargs):
        # Snapshot: the agent keeps mutating its list after the call.
        self.requests.append({**kwargs, "messages": list(kwargs["messages"])})
        return Completion(self.script.pop(0))
