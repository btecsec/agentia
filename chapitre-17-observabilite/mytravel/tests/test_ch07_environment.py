"""Chapter 7: the server answers live, the page is served."""

import json

import httpx
import openai
import pytest
from fastapi.testclient import TestClient

import server


@pytest.fixture
def client():
    return TestClient(server.app)


def events(reply):
    """The Server-Sent Events of a reply, as dicts."""
    return [json.loads(block.removeprefix("data: "))
            for block in reply.text.split("\n\n") if block]


def post(client):
    return client.post("/api/chat", json={
        "message": "Salut", "conversation": "conv-12345"})


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_page_is_served(client):
    page = client.get("/")
    assert page.status_code == 200
    assert "myTravel" in page.text


def test_the_answer_comes_word_by_word(client, monkeypatch):
    def answer(*args):
        yield {"type": "token", "text": "Bon"}
        yield {"type": "token", "text": "jour !"}
        yield {"type": "done", "answer": "Bonjour !"}
    monkeypatch.setattr(server, "stream_mytravel", answer)
    reply = post(client)
    assert reply.headers["content-type"].startswith(
        "text/event-stream")
    assert [e["type"] for e in events(reply)] == [
        "token", "token", "done"]


def test_busy_model_is_said_in_the_stream(client, monkeypatch):
    def busy(*args):
        request = httpx.Request("POST", "https://openrouter.ai")
        raise openai.RateLimitError(
            "busy", response=httpx.Response(429, request=request),
            body=None)
        yield  # a generator, like the real one
    monkeypatch.setattr(server, "stream_mytravel", busy)
    error = events(post(client))[-1]
    assert error["type"] == "error" and "saturé" in error["detail"]


def test_model_errors_stay_on_the_server(client, monkeypatch):
    def broken(*args):
        request = httpx.Request("POST", "https://openrouter.ai")
        raise openai.AuthenticationError(
            "key sk-or-secret expired",
            response=httpx.Response(401, request=request), body=None)
        yield
    monkeypatch.setattr(server, "stream_mytravel", broken)
    reply = post(client)
    assert "regarde" in events(reply)[-1]["detail"]
    assert "sk-or" not in reply.text


def test_unexpected_errors_still_answer(client, monkeypatch):
    def broken(*args):
        yield {"type": "token", "text": "Bon"}
        raise RuntimeError("boom")
    monkeypatch.setattr(server, "stream_mytravel", broken)
    last = events(post(client))[-1]
    assert last["type"] == "error" and "regarde" in last["detail"]
