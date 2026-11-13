"""myTravel as one agent: a prompt, a memory, and its tools.

create_agent builds the loop of chapter 1 on LangGraph: the model
calls tools until it can answer. The checkpointer saves the
conversation after each step, under the conversation id.
"""

from datetime import date

from langchain.agents import create_agent

from app import flights, hotels, tools
from app.memory import checkpointer
from app.modele import get_chat_model

PROMPT = """You are myTravel, a travel assistant. Today is {today}.
Use what the traveler said earlier (nationality, home city,
budget) instead of asking again.
You find and compare; the traveler books and pays on the
provider's website. Use your tools: never answer from memory.
Every fact comes with the URL it was read on. If a tool finds
nothing, say so. Answer in the traveler's language, with short
Markdown sections: flights first, then hotels, then the other
topics.
A price comes from hotel_offers or flight_offers, with its
seller: never a price read elsewhere."""

TOOLS = [
    tools.search_official, tools.read_official_page,
    hotels.hotel_offers, tools.hotel_links, tools.exchange_rate,
    flights.flight_offers, tools.flight_links, tools.car_links,
    tools.weather, tools.travel_advice]

saver = checkpointer()


def stream_mytravel(message, conversation):
    """One message in; each tool call, then the answer, out."""
    prompt = PROMPT.format(today=date.today())
    agent = create_agent(get_chat_model(), TOOLS,
                         system_prompt=prompt, checkpointer=saver,
                         middleware=[tools.tool_errors])
    config = {"configurable": {"thread_id": conversation}}
    for token, _ in agent.stream(
            {"messages": [("user", message)]}, config,
            stream_mode="messages"):
        if token.type == "tool":  # its result: not for the page
            continue
        # The model calls a tool: say it now, it may take a while.
        for call in getattr(token, "tool_call_chunks", []):
            if call["name"]:
                yield {"type": "step", "text": call["name"]}
        if token.content:
            yield {"type": "token", "text": token.content}
    answer = agent.get_state(config).values["messages"][-1]
    yield {"type": "done", "answer": answer.content}
