"""Chapter 8: each conversation is remembered, and only its own."""

from fastapi.testclient import TestClient

import server
from app import graph
from app.graph import Trip
from fakes import fake_model


def test_conversation_is_remembered(monkeypatch):
    model = fake_model(structured=[Trip(question="Quand ?"),
                                   Trip(question="Combien ?")])
    monkeypatch.setattr(graph, "get_chat_model", lambda *a: model)
    graph.ask_mytravel("Je pars à Lisbonne", "conv-memory")
    graph.ask_mytravel("En mai", "conv-memory")
    second_call = " ".join(str(m.content) for m in model.seen[-1])
    assert "Lisbonne" in second_call and "Quand ?" in second_call


def test_conversations_are_separate(monkeypatch):
    model = fake_model(structured=[Trip(question="Quand ?"),
                                   Trip(question="Où ?")])
    monkeypatch.setattr(graph, "get_chat_model", lambda *a: model)
    graph.ask_mytravel("Je pars à Oslo", "conv-a")
    graph.ask_mytravel("Bonjour", "conv-b")
    second_call = " ".join(str(m.content) for m in model.seen[-1])
    assert "Oslo" not in second_call


def test_what_the_traveler_said_comes_back(monkeypatch):
    model = fake_model(structured=[Trip(question="Où ?"),
                                   Trip(question="Quand ?")])
    monkeypatch.setattr(graph, "get_chat_model", lambda *a: model)
    client = TestClient(server.app)
    for message in ["Je suis belge", "Visa pour le Canada ?"]:
        client.post("/api/chat", json={
            "message": message, "conversation": "conv-said"})
    second_call = " ".join(str(m.content) for m in model.seen[-1])
    assert "belge" in second_call
