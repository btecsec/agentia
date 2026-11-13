"""Chapter 1 tests: they run WITHOUT an API key."""

import sys
from pathlib import Path

import pytest

# The chapter folder is self-contained: put it on the import path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent import Agent  # noqa: E402
from fakes import FakeClient, Message, ToolCall  # noqa: E402
from memory import estimate_tokens, trim_messages  # noqa: E402
from tools import calculate, get_weather, search  # noqa: E402


# --- tools ----------------------------------------------------------------


def test_search_finds_a_known_city():
    assert "14 million" in search("Tell me about Tokyo")


def test_search_unknown_city_returns_a_sentence_not_an_error():
    assert "Nothing found" in search("Atlantis")


@pytest.mark.parametrize(
    "expression, expected",
    [("3 * 120", "360"), ("2 ** 10", "1024"), ("-4 + 10", "6"), ("10 / 4", "2.5")],
)
def test_calculate(expression, expected):
    assert calculate(expression) == expected


@pytest.mark.parametrize("hostile", ["__import__('os').system('echo hi')", "abs(-3)"])
def test_calculate_refuses_anything_but_arithmetic(hostile):
    assert "Cannot calculate" in calculate(hostile)


def test_calculate_division_by_zero_is_reported():
    assert "Cannot calculate" in calculate("1 / 0")


def test_weather_is_case_insensitive():
    assert "sunny" in get_weather("LISBON")


# --- the loop -------------------------------------------------------------


def test_answer_without_tool_ends_in_one_call():
    client = FakeClient([Message("Hello!")])
    assert Agent(client=client).chat("Hi") == "Hello!"
    assert len(client.requests) == 1


def test_tool_result_goes_back_to_the_model():
    client = FakeClient(
        [
            Message(tool_calls=[ToolCall("c1", "calculate", {"expression": "3 * 120"})]),
            Message("It costs 360 euros."),
        ]
    )
    answer = Agent(client=client).chat("Cost of 3 nights at 120?")

    assert answer == "It costs 360 euros."
    # The second request must carry the observation, linked by its id.
    tool_message = client.requests[1]["messages"][-1]
    assert tool_message == {"role": "tool", "tool_call_id": "c1", "content": "360"}


def test_two_tools_in_one_turn_are_both_run():
    client = FakeClient(
        [
            Message(
                tool_calls=[
                    ToolCall("a", "get_weather", {"city": "Tokyo"}),
                    ToolCall("b", "search", {"query": "Tokyo"}),
                ]
            ),
            Message("Done."),
        ]
    )
    Agent(client=client).chat("Tokyo?")
    roles = [m["role"] for m in client.requests[1]["messages"]]
    assert roles.count("tool") == 2


def test_unknown_tool_is_reported_to_the_model():
    client = FakeClient([Message(tool_calls=[ToolCall("x", "teleport")]), Message("Sorry.")])
    Agent(client=client).chat("Beam me up")
    assert "does not exist" in client.requests[1]["messages"][-1]["content"]


def test_broken_json_arguments_do_not_crash_the_agent():
    client = FakeClient(
        [Message(tool_calls=[ToolCall("x", "search", "{not json")]), Message("Oops.")]
    )
    assert Agent(client=client).chat("?") == "Oops."
    assert "Error while running" in client.requests[1]["messages"][-1]["content"]


def test_turn_limit_stops_a_looping_agent():
    looping = [Message(tool_calls=[ToolCall(f"c{i}", "search", {"query": "Tokyo"})]) for i in range(10)]
    client = FakeClient(looping)
    answer = Agent(client=client, max_turns=3).chat("Loop")

    assert "Stopped after 3 turns" in answer
    assert len(client.requests) == 3


# --- memory ---------------------------------------------------------------


def test_second_question_sees_the_first():
    client = FakeClient([Message("Tokyo has 14 million people."), Message("Rainy.")])
    agent = Agent(client=client)
    agent.chat("How many people in Tokyo?")
    agent.chat("And the weather there?")

    sent = [m["content"] for m in client.requests[1]["messages"] if m["role"] == "user"]
    assert sent == ["How many people in Tokyo?", "And the weather there?"]


def test_trim_keeps_system_prompt_and_cuts_on_a_user_message():
    messages = [{"role": "system", "content": "s"}]
    for i in range(5):
        messages += [
            {"role": "user", "content": f"q{i}"},
            {"role": "assistant", "content": "", "tool_calls": []},
            {"role": "tool", "tool_call_id": "x", "content": "r"},
            {"role": "assistant", "content": f"a{i}"},
        ]
    trimmed = trim_messages(messages, max_messages=8)

    assert trimmed[0]["role"] == "system"
    assert trimmed[1]["role"] == "user"
    assert len(trimmed) <= 8


def test_trim_does_nothing_when_short():
    messages = [{"role": "system", "content": "s"}, {"role": "user", "content": "q"}]
    assert trim_messages(messages, max_messages=10) == messages


def test_estimate_tokens_grows_with_text():
    short = [{"role": "user", "content": "hi"}]
    long = [{"role": "user", "content": "hi " * 100}]
    assert estimate_tokens(long) > estimate_tokens(short)
