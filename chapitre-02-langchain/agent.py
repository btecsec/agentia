"""myTravel with LangChain: the chapter 1 agent in about 20 lines.

In chapter 1 we wrote the loop "the model asks for a tool, we
run it, we hand back the result".
LangChain ships that loop ready-made.

What disappears: hand-written JSON schemas, reading `tool_calls`,
`tool` messages, the turn counter, the message list.
What stays: your tools. That is the whole point.
"""

from datetime import date

from langchain.agents import create_agent
from langchain_core.prompts import PromptTemplate
from langgraph.checkpoint.memory import InMemorySaver

from modele import get_chat_model
from tools import TOOLKIT

# A PromptTemplate is a text with holes ({today}, {language}) filled
# at the last moment. Same template, different values per user.
SYSTEM_TEMPLATE = PromptTemplate.from_template(
    "You are myTravel, a travel assistant. Today is {today}.\n"
    "Use a tool whenever the answer depends on real-world data "
    "(weather, exchange rates, facts). Never calculate in your "
    "head: use `calculate`. Answer in {language}, in three "
    "sentences max."
)


def build_agent(model=None, language="English", checkpointer=None):
    """Assemble the agent. Tests inject a fake `model`."""
    system_prompt = SYSTEM_TEMPLATE.format(
        today=date.today().isoformat(), language=language
    )
    return create_agent(
        model=model or get_chat_model(),
        tools=TOOLKIT,
        system_prompt=system_prompt,
        # The memory: conversations are saved per `thread_id`.
        checkpointer=checkpointer or InMemorySaver(),
    )


def ask(agent, question, thread_id="trip-1"):
    """Ask a question. Returns (answer, tools called)."""
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {"messages": [("user", question)]}
    result = agent.invoke(inputs, config)
    messages = result["messages"]
    # The thread keeps the whole conversation: only look at this
    # turn, i.e. what follows the last human message.
    humans = [i for i, m in enumerate(messages)
              if m.type == "human"]
    last_human = humans[-1]
    tools_called = [
        call["name"]
        for message in messages[last_human:]
        for call in getattr(message, "tool_calls", [])
    ]
    return messages[-1].content, tools_called
