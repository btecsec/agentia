"""The myTravel graph: who works, and in which order.

    message -> mission -> the agents it chose, in parallel
            -> synthesis -> check_output -> answer

Each node says when it starts, and Synthesis writes word by word:
the page shows both as they happen.

Mission may also stop early: ask a question back (ask_back), or
prepare a booking once a human said yes (confirm). Before the
agents, best_stays prices flights and hotels together.
"""

import operator
from datetime import date
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import (AIMessage, HumanMessage,
                                     SystemMessage)
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.config import get_stream_writer
from langgraph.types import Command, Send, interrupt
from pydantic import BaseModel, Field

from app.agents import AGENTS, run_agent
from app.guardrails import clean_answer, links_in
from app.logs import log
from app.memory import checkpointer
from app.modele import get_chat_model
from app.stays import choices, packages, stay_text, stays
from app.tools import booking_url, cars_url, flights_url


class Trip(BaseModel):
    """What the Mission agent understood from the conversation."""
    destination: str = Field("", description="City or country")
    country: str = Field("", description="Country of destination")
    start: str = Field("", description="First day, YYYY-MM-DD")
    end: str = Field("", description="Last day, YYYY-MM-DD")
    origin: str = Field("", description="City the traveler leaves")
    nationality: str = Field("", description="Traveler's passport")
    travelers: int = 1
    budget: str = ""
    agents: list[Literal["admin", "hotel", "transport", "weather",
                         "risk"]] = Field(
        default_factory=list,
        description="Agents needed for the last message")
    question: str = Field(
        "", description="Question to ask back if something "
                        "essential is missing, else empty")
    booking: bool = Field(
        False, description="True if the traveler asks to prepare "
                           "the booking of the plan")
    flexible: int = Field(
        0, description="Days the traveler may move the trip, "
                       "before or after; 0 if the dates are fixed")


def fresh(old, new):
    """Parallel agents add to the list; [] starts it over."""
    return old + new if new else []


class State(TypedDict):
    messages: Annotated[list, add_messages]  # the conversation
    trip: dict
    reports: Annotated[list, fresh]  # (agent, report) pairs
    steps: Annotated[list, fresh]  # shown in the page
    answer: str
    sources: list
    # Every URL a tool returned in this conversation: the only
    # links an answer may hold. Added up, never started over.
    found: Annotated[list, operator.add]


MISSION = """You are the Mission agent of myTravel. Today is
{today}. Read the whole conversation and fill in the trip: the
traveler may have given their nationality, home city or budget
in an earlier message. Choose only the agents the LAST message
needs:
- admin: visa, passport, entry rules, health, baggage, customs
- hotel: where to sleep
- transport: flights, rental car
- weather: weather on the dates
- risk: safety, natural risks
A request for a full trip plan needs all five.
A stay, flight and hotel together, needs transport and hotel.
Ask a question back only if:
- the destination is unknown,
- dates are needed and missing,
- the traveler gives a period to travel in ("entre le 22
  janvier et le 8 mars") but not how long the trip lasts: ask
  how long; once said, the trip starts on the period's first day,
- a visa question needs the nationality and nobody gave it.
Never ask anything else: the agents choose cities and hotels.
The question says what you understood, then names every missing
piece at once and why you need it: "Thaïlande, à deux, depuis
Paris : noté. Il me manque la durée du voyage, pour chercher
les vols et les hôtels : combien de jours veux-tu partir ?",
in the traveler's language. Set booking to true only if the
traveler asks to prepare the booking of a plan already given
("réserve", "prépare la réservation"): then choose no agent.
If an answer moved the dates to cheaper days, use the new
dates."""

SYNTHESIS = """You are the Synthesis agent of myTravel. Answer the
traveler's last message in their language, from the agents'
reports below and nothing else. Be clear and warm, use short
Markdown sections in the order of the reports, a section only
for a report below. A flight offer is a real one: give its
price, seller, the day it was seen and its link, never call it
an estimate. A hotel price is today's price of a night: give it
with its seller and its links.
A stay is flight and hotel on the same days: give each stay
with its dates, flight, hotel, sellers, total and links, in
their order, and say if the dates moved. An agency package
gives a catalog price, "dès" a person: say so, with its agency
and link, and never add it to a total.
The stay lasts {nights} nights: never count another length.
Check the total against the budget. Keep every URL of the
reports next to the fact it supports, copied exactly: a URL you
change or write yourself is removed. End with a "Sources" list.
If a report found nothing, say so plainly. Never write a fact no
report gives: a direct flight, a full flight, a star rating.
Reminder: myTravel compares, the traveler books.

Trip: {trip}

{reports}"""

# The answer always opens on the stays, the agencies' packages,
# flights, then hotels.
ORDER = ["stays", "packages", "transport", "hotel", "admin",
         "weather", "risk"]

# Said when Mission could not read the message at all: what a
# request needs, so the traveler knows what to write.
UNREAD = ("Je n'ai pas réussi à lire ta demande. Donne-moi la "
          "destination, les dates (ou la période et la durée), "
          "ta ville de départ et le nombre de voyageurs.")


def mission(state):
    get_stream_writer()("Mission")  # shown now, in the page
    model = get_chat_model().with_structured_output(
        Trip, method="function_calling")
    prompt = MISSION.format(today=date.today())
    for _ in range(2):  # a free model may answer nothing
        try:
            trip = model.invoke([SystemMessage(prompt),
                                 *state["messages"]])
        except ValueError:  # the fiche does not match Trip
            trip = None
        if trip is not None:
            break
    if trip is None:  # twice nothing, or prose
        trip = Trip(question=UNREAD)
    trip.start, trip.end = not_past(trip.start), not_past(trip.end)
    log("mission", destination=trip.destination,
        agents=trip.agents)
    return {"trip": trip.model_dump(), "steps": ["Mission"]}


def not_past(day):
    """A model reads "22 janvier" in November as the one gone by:
    the traveler means next year's."""
    try:
        if date.fromisoformat(day) < date.today():
            return f"{int(day[:4]) + 1}{day[4:]}"
    except ValueError:  # no date given
        pass
    return day


def after_mission(state):
    """The road after Mission: a question, a booking, or agents."""
    trip = state["trip"]
    if trip["question"]:
        return "ask_back"
    if trip["booking"]:
        return "confirm"
    if trip["start"] and ("hotel" in trip["agents"] or (
            "transport" in trip["agents"] and trip["flexible"])):
        return "best_stays"
    return send_agents(state)


def send_agents(state):
    trip = state["trip"]
    request = state["messages"][-1].content
    # Send = "run this node with this input": one per agent, and
    # LangGraph runs them at the same time.
    return [Send("agent", {"name": name, "trip": trip,
                           "request": request})
            for name in trip["agents"]] or "synthesis"


def best_stays(state):
    """Flights and hotels priced together, by code, before the
    agents: the trip moves to the days of the best value stay."""
    get_stream_writer()("Séjours clé en main")
    trip = dict(state["trip"])
    try:
        found = stays(trip)
    except Exception as error:  # no token, unknown city: the agents
        log("best_stays_failed", error=str(error))
        found = []
    agencies = packages(trip["destination"])
    sold = []  # the agencies' packages, if any was found
    if agencies:
        sold = [("packages", "## Séjours des agences de voyages\n"
                 "Prix d'appel des catalogues, par personne, à "
                 "vérifier aux dates :\n" + agencies)]
    if not found:  # the agents search flights and hotels apart
        return {"steps": ["Séjours : aucune offre"],
                "reports": sold, "found": links_in(agencies)}
    asked = (trip["start"], trip["end"])
    before = next((s["total"] for s in found
                   if (s["out"], s["back"]) == asked), None)
    best = choices(found)[:3]
    trip["start"], trip["end"] = best[0]["out"], best[0]["back"]
    # The stays hold the hotels, and the flights if any was seen.
    done = ["hotel"] + ["transport"] * ("fare" in best[0])
    trip["agents"] = [name for name in trip["agents"]
                      if name not in done]
    report = "\n".join(
        ["## Séjours clé en main", "Prix réels vus, total pour "
         f"{trip['travelers']}, du meilleur rapport qualité-prix "
         "(prix par point de note) au moins bon :"]
        + [stay_text(s, trip["travelers"]) for s in best])
    if (trip["start"], trip["end"]) != asked:
        report += (f"\nDates déplacées au {trip['start']} -> "
                   f"{trip['end']}, {nights(trip)} nuits au lieu "
                   f"de {nights(state['trip'])}. Aux dates "
                   "demandées : " +
                   (f"{before} €." if before else "aucune offre."))
    return {"trip": trip, "steps": ["Séjours clé en main"],
            "reports": [("stays", report), *sold],
            "found": links_in(report + agencies)}


def agent(task):
    get_stream_writer()(AGENTS[task["name"]]["label"])
    report, used, found = run_agent(task["name"], task["trip"],
                                    task["request"])
    step = AGENTS[task["name"]]["label"]
    if used:  # the page shows them in another color
        step += f" ({', '.join(used)})"
    return {"reports": [(task["name"], report)], "steps": [step],
            "found": found}


def synthesis(state):
    get_stream_writer()("Synthèse")
    ranked = sorted(state["reports"],
                    key=lambda pair: ORDER.index(pair[0]))
    reports = "\n\n".join(report for _, report in ranked)
    prompt = SYNTHESIS.format(trip=state["trip"],
                              nights=nights(state["trip"]),
                              reports=reports or "No report.")
    answer = get_chat_model().invoke(
        [SystemMessage(prompt), *state["messages"]]).content
    return {"answer": answer, "steps": ["Synthèse"]}


def nights(trip):
    """Counted here: a model that counts days writes 47 for 16."""
    try:
        return (date.fromisoformat(trip["end"])
                - date.fromisoformat(trip["start"])).days
    except ValueError:  # no dates: a visa question, say
        return "an unknown number of"


def ask_back(state):
    question = state["trip"]["question"]
    return {"answer": question, "messages": [AIMessage(question)]}


def confirm(state):
    trip = state["trip"]
    # The graph stops here and saves itself. The page shows the
    # question; /api/confirm resumes with True or False.
    approved = interrupt(
        f"Je prépare les liens de réservation pour "
        f"{trip['destination']}, du {trip['start']} au "
        f"{trip['end']}, {trip['travelers']} voyageur(s). "
        f"On y va ?")
    if not approved:
        return {"answer": "D'accord, je ne prépare rien.",
                "steps": ["Réservation annulée"]}
    sheet = booking_sheet(trip)
    return {"answer": sheet, "found": links_in(sheet),
            "steps": ["Réservation préparée"]}


def booking_sheet(trip):
    """Links filled with the trip: the traveler books, not us."""
    city, people = trip["destination"], trip["travelers"]
    start, end = trip["start"], trip["end"]
    flights = flights_url(trip["origin"], city, start, end, people)
    hotels = booking_url(city, start, end, people)
    return (
        f"### Ta fiche de réservation : {city}\n\n"
        f"1. **Vols** : [Google Flights]({flights})\n"
        f"2. **Hôtel** : [Booking.com]({hotels})\n"
        f"3. **Voiture** (si besoin) : [Kayak]("
        f"{cars_url(city, start, end)})\n\n"
        "Avant de payer : vérifie les dates, le nom sur le "
        "passeport, et les conditions d'annulation.")


def check_output(state):
    answer, sources = clean_answer(state["answer"], state["found"])
    return {"answer": answer, "sources": sources,
            "messages": [AIMessage(answer)]}


def build_graph():
    graph = StateGraph(State)
    graph.add_node("mission", mission)
    graph.add_node("best_stays", best_stays)
    graph.add_node("agent", agent)
    graph.add_node("synthesis", synthesis)
    graph.add_node("ask_back", ask_back)
    graph.add_node("confirm", confirm)
    graph.add_node("check_output", check_output)
    graph.add_edge(START, "mission")
    graph.add_conditional_edges(
        "mission", after_mission,
        ["agent", "synthesis", "ask_back", "confirm", "best_stays"])
    graph.add_conditional_edges("best_stays", send_agents,
                                ["agent", "synthesis"])
    graph.add_edge("agent", "synthesis")  # waits for all agents
    graph.add_edge("synthesis", "check_output")
    graph.add_edge("confirm", "check_output")
    graph.add_edge("check_output", END)
    graph.add_edge("ask_back", END)
    return graph.compile(checkpointer=checkpointer())


graph = build_graph()


def stream_mytravel(message, conversation, paid=False):
    """One message in; events out, as they happen."""
    start = {"messages": [HumanMessage(message)], "reports": [],
             "steps": [], "answer": "", "sources": []}
    return run(start, conversation, paid)


def stream_confirm(conversation, approved):
    """The human's answer. None if no booking was waiting."""
    config = {"configurable": {"thread_id": conversation}}
    if not graph.get_state(config).interrupts:
        return None
    return run(Command(resume=approved), conversation)


def run(start, conversation, paid=False):
    """The graph, streamed: "custom" carries what the nodes say
    with get_stream_writer, "messages" the model's tokens."""
    config = {"configurable": {"thread_id": conversation,
                               "paid": paid}}
    for mode, chunk in graph.stream(start, config,
                                    stream_mode=["custom",
                                                 "messages"]):
        if mode == "custom":
            yield {"type": "step", "text": chunk}
        elif (chunk[1]["langgraph_node"] == "synthesis"
              and chunk[0].content):  # not the specialists' drafts
            yield {"type": "token", "text": chunk[0].content}
    yield {"type": "done", **reply(graph.get_state(config))}


def ask_mytravel(message, conversation):
    """The whole reply at once: for the tests and evaluate.py."""
    return list(stream_mytravel(message, conversation))[-1]


def reply(snapshot):
    state, waiting = snapshot.values, snapshot.interrupts
    return {"answer": state["answer"], "sources": state["sources"],
            "steps": state["steps"],
            "confirm": waiting[0].value if waiting else None}
