"""A scripted CrewAI model: replays answers, records prompts.

CrewAI asks its agents to answer in a ReAct format. The final answer
must follow "Final Answer:", so the helper `final()` adds it.
"""

from crewai import BaseLLM


def final(text):
    return f"Thought: I have what I need.\nFinal Answer: {text}"


class ScriptedLLM(BaseLLM):
    llm_type: str = "scripted"

    def __init__(self, *answers):
        super().__init__(model="scripted")
        self._answers = list(answers)
        self.prompts = []

    def call(self, messages, tools=None, callbacks=None,
             available_functions=None, from_task=None,
             from_agent=None, **kwargs):
        self.prompts.append(messages)
        return self._answers.pop(0)

    def supports_function_calling(self):
        return False

    def get_context_window_size(self):
        return 8000

    def prompt_text(self, index):
        """All the text the model received on call number `index`."""
        return " ".join(m["content"] for m in self.prompts[index])
