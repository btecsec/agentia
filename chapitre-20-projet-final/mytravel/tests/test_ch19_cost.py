"""Chapter 19: fewer requests, a cheaper model where it is enough."""

import json

import httpx
from langchain_core.runnables import RunnableLambda
from fastapi.testclient import TestClient
from openai import RateLimitError

import server
from app.security import RateLimiter
from app import agents, modele, web


def test_same_search_twice_asks_the_engine_once(monkeypatch):
    calls = []

    def engine(query, domains):
        calls.append(query)
        return [{"title": "t", "snippet": "s",
                 "url": "https://www.diplomatie.gouv.fr/x"}]
    monkeypatch.setattr(web, "search_engine", engine)
    web.search_web("visa Islande cache", ["diplomatie.gouv.fr"])
    found = web.search_web("visa Islande cache",
                           ["diplomatie.gouv.fr"])
    assert len(calls) == 1 and len(found) == 1


def test_agents_use_the_fast_model(monkeypatch):
    asked = []

    def model(name):
        asked.append(name)
    monkeypatch.setattr(agents, "get_chat_model", model)
    monkeypatch.setattr(agents, "create_agent", lambda *a, **k: None)
    try:
        agents.run_agent("weather", {}, "Météo ?")
    except AttributeError:  # the fake agent cannot run: fine
        pass
    assert asked == [modele.FAST_MODEL]


def busy(*args):
    request = httpx.Request("POST", "https://openrouter.ai")
    raise RateLimitError("busy", body=None,
                         response=httpx.Response(429, request=request))
    yield  # a generator, like the real one


def last_event(reply):
    return json.loads(reply.text.strip().split("\n\n")[-1][6:])


def test_free_models_busy_offers_the_paid_one(monkeypatch):
    monkeypatch.setattr(server, "stream_mytravel", busy)
    reply = TestClient(server.app).post("/api/chat", json={
        "message": "Salut", "conversation": "conv-12345"})
    assert last_event(reply)["paid_offer"] == modele.PAID_MODEL
    assert last_event(reply)["token"]


def test_paid_model_only_with_the_servers_offer(monkeypatch):
    used = []

    def ask(message, conversation, paid):
        used.append(paid)
        yield {"type": "done", "answer": "ok"}
    monkeypatch.setattr(server, "limiter", RateLimiter(99))
    client = TestClient(server.app)

    def post(token=""):
        return client.post("/api/chat", json={
            "message": "Salut", "conversation": "conv-12345",
            "paid": token})

    def offer():
        monkeypatch.setattr(server, "stream_mytravel", busy)
        token = last_event(post())["token"]
        monkeypatch.setattr(server, "stream_mytravel", ask)
        return token
    token = offer()
    post(token)  # yes: the paid model
    post(token)  # the same token again: free
    offer()
    post("forged-by-a-page")  # free
    assert used == [True, False, False]


def test_a_paid_run_uses_the_paid_model():
    def model(_):
        return modele.get_chat_model().model_name
    run = RunnableLambda(model)
    assert run.invoke(None) == modele.MODEL
    paid = {"configurable": {"paid": True}}
    assert run.invoke(None, paid) == modele.PAID_MODEL
