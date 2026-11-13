"""myTravel v1: a model, tools, a loop. No framework.

Everything is written by hand so you can see the loop that
frameworks hide in the next chapters.
"""

import json

from modele import MODEL, get_client
from tools import TOOL_SCHEMAS, TOOLS

SYSTEM_PROMPT = """You are myTravel, a travel assistant.
You have tools. Rules:
- Never guess a fact a tool can give you.
- Never calculate in your head: call `calculate`.
- When you have what you need, answer in one or two sentences."""


class Agent:
    """A model + tools + a loop + a turn limit + a memory."""

    def __init__(self, client=None, model=MODEL, max_turns=6,
                 verbose=False):
        # A fake client can be injected: tests run without a key.
        self.client = client or get_client()
        self.model = model
        # Without a limit, a lost agent loops (and bills) forever.
        self.max_turns = max_turns
        self.verbose = verbose
        # The memory IS this list: the model only knows its content.
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    def chat(self, question):
        """Ask a question; the conversation is kept for the next."""
        self.messages.append({"role": "user", "content": question})

        for turn in range(1, self.max_turns + 1):
            # REASON: the model reads it all and decides.
            reply = self.client.chat.completions.create(
                model=self.model,
                tools=TOOL_SCHEMAS,
                messages=self.messages,
            ).choices[0].message
            message = reply.model_dump(exclude_none=True)
            self.messages.append(message)

            # No tool requested: this is the final answer. We stop.
            if not reply.tool_calls:
                return reply.content or ""

            for call in reply.tool_calls:
                name = call.function.name
                args = call.function.arguments
                # ACT: our code runs the tool, not the model.
                result = self._run_tool(name, args)
                self._log(turn, name, args, result)
                # OBSERVE: the result goes back in the conversation.
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result,
                })

        return f"Stopped after {self.max_turns} turns, no answer."

    def _run_tool(self, name, arguments_json):
        """Run a tool. Always returns text, even on error."""
        if name not in TOOLS:
            return f"Error: tool {name!r} does not exist."
        try:
            # Arguments arrive as JSON text written by a model:
            # it may be broken.
            arguments = json.loads(arguments_json or "{}")
            return str(TOOLS[name](**arguments))
        except Exception as error:  # noqa: BLE001
            # The error goes back to the model, which can adapt.
            return f"Error while running {name}: {error}"

    def _log(self, turn, name, arguments, result):
        if self.verbose:
            print(f"  [turn {turn}] ACT     {name}({arguments})")
            print(f"  [turn {turn}] OBSERVE {result}")
