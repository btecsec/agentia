"""myTravel as one agent: a prompt and a memory.

create_agent builds a small LangGraph graph around the model.
No tools yet (chapter 9): what matters here is the
checkpointer, which saves the conversation after each step,
under the conversation id.
"""

from datetime import date

from langchain.agents import create_agent

from app.memory import checkpointer
from app.modele import get_chat_model

PROMPT = """You are myTravel, a travel assistant. Today is {today}.
Use what the traveler said earlier (nationality, home city,
budget) instead of asking again.
You find and compare; the traveler books and pays on the
provider's website. Answer in the traveler's language, with short
Markdown sections."""

saver = checkpointer()


def stream_mytravel(message, conversation):
    """One message in; the answer out, word by word."""
    prompt = PROMPT.format(today=date.today())
    agent = create_agent(get_chat_model(), [],
                         system_prompt=prompt, checkpointer=saver)
    config = {"configurable": {"thread_id": conversation}}
    # "messages": the model's tokens, as it writes them.
    for token, _ in agent.stream(
            {"messages": [("user", message)]}, config,
            stream_mode="messages"):
        if token.content:
            yield {"type": "token", "text": token.content}
    answer = agent.get_state(config).values["messages"][-1]
    yield {"type": "done", "answer": answer.content}
