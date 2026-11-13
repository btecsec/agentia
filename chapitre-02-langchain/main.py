"""Run chapter 2:  python main.py

Needs OPENROUTER_API_KEY in the .env file at the repository root.
"""

import sys

from openai import RateLimitError

from agent import ask, build_agent

# The agent is built ONCE and keeps the conversation under one
# thread_id: the second question relies on the first.
QUESTIONS = [
    "Give me two facts about Lisbon.",
    "What is the weather there right now?",
    "What do 250 euros make in Japanese yen?",
]


def main():
    agent = build_agent()
    for question in QUESTIONS:
        answer, tools_called = ask(agent, question)
        print(f"\n> {question}")
        print(f"  tools: {tools_called or 'none'}")
        print(f"< {answer}")


if __name__ == "__main__":
    try:
        main()
    except RateLimitError:
        # Free quotas are shared by everyone: it is not your code.
        sys.exit("The model is saturated (429). Wait a minute, or "
                 "change MODELE in .env (python modele.py).")
