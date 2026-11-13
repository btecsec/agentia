"""A scripted stand-in for the chat model.

The graph only calls `model.invoke(prompt).content`, so the double
only needs that. It records every prompt: tests can count the model
calls and read what each node asked.
"""

from types import SimpleNamespace


class ScriptedModel:
    def __init__(self, *answers):
        self.answers = list(answers)
        self.prompts = []

    def invoke(self, prompt):
        self.prompts.append(prompt)
        return SimpleNamespace(content=self.answers.pop(0))

    @property
    def calls(self):
        return len(self.prompts)
