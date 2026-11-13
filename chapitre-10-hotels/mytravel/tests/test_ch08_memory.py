"""Chapter 8: each conversation is remembered, and only its own."""

from fastapi.testclient import TestClient

import server
from app import assistant
from fakes import fake_model


def ask(message, conversation):
    return list(assistant.stream_mytravel(message, conversation))


def plug(monkeypatch, *answers):
    model = fake_model(*answers)
    monkeypatch.setattr(assistant, "get_chat_model", lambda: model)
    return model


def test_conversation_is_remembered(monkeypatch):
    model = plug(monkeypatch, "Quand ?", "Combien ?")
    ask("Je pars à Lisbonne", "conv-memory")
    ask("En mai", "conv-memory")
    second_call = " ".join(str(m.content) for m in model.seen[-1])
    assert "Lisbonne" in second_call and "Quand ?" in second_call


def test_conversations_are_separate(monkeypatch):
    model = plug(monkeypatch, "Quand ?", "Où ?")
    ask("Je pars à Oslo", "conv-a")
    ask("Bonjour", "conv-b")
    second_call = " ".join(str(m.content) for m in model.seen[-1])
    assert "Oslo" not in second_call


def test_the_answer_comes_word_by_word(monkeypatch):
    plug(monkeypatch, "Bonjour, où veux-tu aller ?")
    events = ask("Salut", "conv-words")
    words = [e["text"] for e in events if e["type"] == "token"]
    assert len(words) > 1
    assert events[-1] == {"type": "done",
                          "answer": "Bonjour, où veux-tu aller ?"}


def test_what_the_traveler_said_comes_back(monkeypatch):
    model = plug(monkeypatch, "Où ?", "Quand ?")
    client = TestClient(server.app)
    for message in ["Je suis belge", "Visa pour le Canada ?"]:
        client.post("/api/chat", json={
            "message": message, "conversation": "conv-said"})
    second_call = " ".join(str(m.content) for m in model.seen[-1])
    assert "belge" in second_call
