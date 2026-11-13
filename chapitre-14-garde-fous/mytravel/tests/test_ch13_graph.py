"""Chapter 13: Mission picks the agents, they work in parallel."""

from app import agents, graph
from app.graph import Trip
from fakes import fake_model, looping_model, tool_call

TOKYO = dict(destination="Tokyo", country="Japon",
             start="2027-03-10", end="2027-03-20")


def plug(monkeypatch, trip, synthesis="Voici ton plan."):
    model = fake_model(synthesis, structured=[trip])
    monkeypatch.setattr(graph, "get_chat_model", lambda *a: model)
    ran = []

    def run_agent(name, trip, request):
        ran.append(name)
        return f"{name} report", []
    monkeypatch.setattr(graph, "run_agent", run_agent)
    return model, ran


def test_mission_calls_only_the_needed_agents(monkeypatch):
    model, ran = plug(monkeypatch, Trip(**TOKYO, agents=["admin"]))
    graph.ask_mytravel("Visa pour le Japon ?", "conv-g1")
    assert ran == ["admin"]


def test_reports_reach_synthesis_flights_first(monkeypatch):
    model, ran = plug(monkeypatch, Trip(
        **TOKYO, agents=["weather", "hotel", "transport"]))
    reply = graph.ask_mytravel("Plan complet", "conv-g2")
    assert sorted(ran) == ["hotel", "transport", "weather"]
    prompt = str(model.seen[-1][0].content)
    assert (prompt.index("transport report")
            < prompt.index("hotel report")
            < prompt.index("weather report"))
    assert reply["answer"] == "Voici ton plan."


def test_missing_information_asks_back(monkeypatch):
    model, ran = plug(monkeypatch, Trip(question="Où veux-tu aller ?"))
    reply = graph.ask_mytravel("Je veux partir", "conv-g3")
    assert reply["answer"] == "Où veux-tu aller ?"
    assert ran == []


def test_an_agent_is_a_real_tool_loop(monkeypatch):
    model = looping_model("Pas de visa pour 90 jours.")
    monkeypatch.setattr(agents, "get_chat_model", lambda *a: model)
    report, found = agents.run_agent("admin", TOKYO, "Visa ?")
    assert "Pas de visa" in report


def test_unreadable_mission_asks_back(monkeypatch):
    model, ran = plug(monkeypatch, None)
    model.structured.append(None)  # Mission tries twice
    reply = graph.ask_mytravel("???", "conv-g4")
    assert "destination" in reply["answer"] and ran == []


def test_a_broken_tool_does_not_break_the_agent(monkeypatch):
    model = fake_model(tool_call("weather", city="Rome",
                                 start="mars", end="avril"),
                       "Je n'ai pas pu lire la météo.")
    monkeypatch.setattr(agents, "get_chat_model", lambda *a: model)
    report, found = agents.run_agent("weather", {}, "Météo ?")
    assert "pas pu" in report


def test_steps_come_first_then_the_answer_word_by_word(
        monkeypatch):
    plug(monkeypatch, Trip(**TOKYO, agents=["weather"]))
    events = list(graph.stream_mytravel("Météo ?", "conv-g5"))
    steps = [e["text"] for e in events if e["type"] == "step"]
    words = [e["text"] for e in events if e["type"] == "token"]
    assert steps == ["Mission", "Météo", "Synthèse"]
    assert len(words) > 1 and "".join(words) == "Voici ton plan."
    assert events[-1]["type"] == "done"
