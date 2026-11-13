"""Chapter 16: automatic checks on real answers."""

import json
from pathlib import Path

from app import graph
from app.evaluation import check_case
from app.graph import Trip
from fakes import fake_model

CASES = Path(__file__).parent.parent / "data" / "eval_cases.json"
CASE = {"question": "Visa Japon ?", "agents": ["Administration"],
        "must_cite": ["diplomatie.gouv.fr"], "must_say": ["passeport"]}


def test_a_good_answer_passes():
    reply = {"answer": "Ton passeport suffit.", "steps": [
        "Mission", "Administration (search_official)", "Synthèse"],
        "sources": ["https://www.diplomatie.gouv.fr/fr/japon/"]}
    assert check_case(CASE, reply) == []


def test_a_bad_answer_lists_its_problems():
    reply = {"answer": "Pas d'idée.", "steps": ["Mission"],
             "sources": []}
    problems = check_case(CASE, reply)
    assert len(problems) == 3


def test_cases_file_is_valid():
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    assert len(cases) >= 5
    assert all("question" in case for case in cases)


def test_steps_are_returned(monkeypatch):
    model = fake_model("Plan.", structured=[Trip(
        destination="Rome", agents=["weather"])])
    monkeypatch.setattr(graph, "get_chat_model", lambda *a: model)
    monkeypatch.setattr(graph, "run_agent",
                        lambda *a: ("sunny", ["weather"], []))
    reply = graph.ask_mytravel("Météo à Rome ?", "conv-e1")
    assert reply["steps"] == ["Mission", "Météo (weather)",
                              "Synthèse"]
