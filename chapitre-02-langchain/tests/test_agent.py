"""Chapter 2 tests: no key, no network (a fake model, a fake web)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import tools  # noqa: E402
from agent import SYSTEM_TEMPLATE, ask, build_agent  # noqa: E402
from fake_model import answer, model_that_says, tool_call  # noqa: E402


@pytest.fixture
def fake_web(monkeypatch):
    """Replace the network door with canned JSON, keyed by URL part."""
    pages = {
        "wikipedia": {"extract": "Lisbon is the capital of Portugal."},
        "geocoding": {
            "results": [
                {"name": "Tokyo", "country": "Japan",
                 "latitude": 35.7, "longitude": 139.7}
            ]
        },
        "forecast": {"current": {"temperature_2m": 18.5}},
        "frankfurter": {"rates": {"JPY": 160.0}},
    }

    def fake_get_json(url, params=None):
        for key, payload in pages.items():
            if key in url:
                return payload
        raise AssertionError(f"unexpected URL {url}")

    monkeypatch.setattr(tools, "_get_json", fake_get_json)
    return pages


# --- tools: the schema is built for us ---------------------------------


def test_every_tool_is_a_langchain_tool_with_a_description():
    names = {t.name for t in tools.TOOLKIT}
    assert names == {"web_search", "calculate", "get_weather",
                     "convert_currency"}
    assert all(t.description for t in tools.TOOLKIT)


def test_schema_comes_from_signature_and_docstring():
    schema = tools.convert_currency.args
    assert set(schema) == {"amount", "source", "target"}
    assert schema["source"]["description"].startswith("The ISO code")


def test_web_search_returns_the_summary(fake_web):
    assert "capital of Portugal" in tools.web_search.invoke("Lisbon")


def test_web_search_network_error_is_a_sentence(monkeypatch):
    def broken(url, params=None):
        raise OSError("offline")

    monkeypatch.setattr(tools, "_get_json", broken)
    assert "No result" in tools.web_search.invoke("Lisbon")


def test_weather(fake_web):
    assert "18.5" in tools.get_weather.invoke({"city": "Tokyo"})


def test_weather_unknown_city(fake_web):
    fake_web["geocoding"] = {}
    assert "Unknown city" in tools.get_weather.invoke({"city": "Xyz"})


def test_convert_currency(fake_web):
    result = tools.convert_currency.invoke(
        {"amount": 250, "source": "eur", "target": "jpy"}
    )
    assert result == "250.0 EUR = 40000.00 JPY"


def test_calculate_is_safe():
    assert tools.calculate.invoke("3 * 120") == "360"
    refused = tools.calculate.invoke("__import__('os').getcwd()")
    assert "Cannot calculate" in refused


# --- the agent -----------------------------------------------------------


def test_prompt_template_fills_its_holes():
    text = SYSTEM_TEMPLATE.format(today="2026-05-01", language="French")
    assert "2026-05-01" in text and "French" in text


def test_tool_is_run_then_the_model_concludes(fake_web):
    fake = model_that_says(
        tool_call("get_weather", {"city": "Tokyo"}),
        answer("18.5 degrees in Tokyo."),
    )
    text, called = ask(build_agent(model=fake), "Weather in Tokyo?")

    assert called == ["get_weather"]
    assert text == "18.5 degrees in Tokyo."


def test_question_without_tool_is_answered_directly():
    agent = build_agent(model=model_that_says(answer("Hello!")))
    assert ask(agent, "Hi") == ("Hello!", [])


def test_memory_is_kept_per_thread():
    fake = model_that_says(answer("one"), answer("two"), answer("three"))
    agent = build_agent(model=fake)
    ask(agent, "first", thread_id="A")
    ask(agent, "second", thread_id="A")
    ask(agent, "other conversation", thread_id="B")

    history_a = agent.get_state({"configurable": {"thread_id": "A"}})
    history_b = agent.get_state({"configurable": {"thread_id": "B"}})
    # system prompt is not stored; 2 questions + 2 answers in A, 1+1 in B.
    assert len(history_a.values["messages"]) == 4
    assert len(history_b.values["messages"]) == 2
