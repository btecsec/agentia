"""The specialist agents: a prompt and a few tools each.

An agent here is the loop of chapter 1, built by LangChain on
LangGraph: the model calls tools until it can answer. Five small
agents with two or three tools choose better than one agent
with ten.
"""

from langchain.agents import create_agent

from app import flights, hotels, tools
from app.guardrails import links_in
from app.modele import get_chat_model

COMMON = """You are the {label} agent of myTravel, a travel
assistant. You find and compare; the traveler books and pays on
the provider's website. Use your tools: never answer from memory.
Every fact comes with the URL it was read on. If a tool finds
nothing, say so. Write a short report in French for the
Synthesis agent.
"""

AGENTS = {
    "admin": {
        "label": "Administration",
        "tools": [tools.search_official, tools.read_official_page],
        "prompt": "Visa, passport validity, entry rules, health, "
                  "baggage and customs, for the traveler's "
                  "nationality. Read the official page before "
                  "citing it.",
    },
    "hotel": {
        "label": "Hôtel",
        "tools": [hotels.hotel_offers, tools.hotel_links,
                  tools.exchange_rate],
        "prompt": "Two or three hotels within budget, with "
                  "today's price of a night on the trip dates "
                  "and its seller, from hotel_offers. Without "
                  "dates, ask for them and give hotel_links: "
                  "never a price read elsewhere.",
    },
    "transport": {
        "label": "Transports",
        "tools": [flights.flight_offers, tools.flight_links,
                  tools.car_links],
        "prompt": "The cheapest flights on the trip dates, with "
                  "their real price, from flight_offers, and if "
                  "useful a rental car. If flight_offers finds no "
                  "offer, say so and give flight_links: never a "
                  "price read elsewhere. Give the links.",
    },
    "weather": {
        "label": "Météo",
        "tools": [tools.weather],
        "prompt": "The weather on the trip dates, and what to pack "
                  "for it.",
    },
    "risk": {
        "label": "Risque",
        "tools": [tools.travel_advice, tools.search_official],
        "prompt": "Safety level, areas to avoid, natural and "
                  "health risks, from the official travel advice.",
    },
}


# A tool that failed proves nothing, even if it names a URL.
FAILED = ("Could not read", "Tool error")


def tool_links(messages):
    """(pages read and links made, every URL the tools returned)."""
    made, found = [], []
    for message in messages:
        text = message.content
        if message.type != "tool" or text.startswith(FAILED):
            continue
        found += links_in(text)
        # Search results are many: the model picks among them.
        if not message.name.startswith("search_"):
            made += links_in(text)
    return list(dict.fromkeys(made)), list(dict.fromkeys(found))


def run_agent(name, trip, request):
    """One agent, one task: its report and the URLs its
    tools returned."""
    spec = AGENTS[name]
    agent = create_agent(
        get_chat_model(), spec["tools"],
        system_prompt=COMMON.format(label=spec["label"])
        + spec["prompt"],
        middleware=[tools.tool_errors])
    task = f"Traveler's message: {request}\nTrip: {trip}"
    result = agent.invoke({"messages": [("user", task)]})
    report = f"## {spec['label']}\n{result['messages'][-1].content}"
    made, found = tool_links(result["messages"])
    if made:  # written by the code: the model may forget them
        report += "\nSources : " + " ".join(made)
    return report, found
