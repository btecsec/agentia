"""Run chapter 1:  python main.py

Needs OPENROUTER_API_KEY in the .env file at the repository root.
"""

import sys

from openai import RateLimitError

from agent import Agent
from memory import estimate_tokens, trim_messages

# One conversation, three questions. The second only makes sense
# thanks to the memory: "there" is the city of the first question.
QUESTIONS = [
    "How many people live in Tokyo?",
    "What is the weather there, and what do 3 nights at 120 euros "
    "cost?",
    "And the weather in Lisbon?",
]


def main():
    # One agent for the whole conversation: it keeps its memory.
    agent = Agent(verbose=True)
    for question in QUESTIONS:
        print(f"\n> {question}")
        print(f"< {agent.chat(question)}")
        # Keep the context window under control between questions.
        agent.messages = trim_messages(agent.messages, 20)
        tokens = estimate_tokens(agent.messages)
        print(f"  (about {tokens} tokens in context)")


if __name__ == "__main__":
    try:
        main()
    except RateLimitError:
        # Free quotas are shared by everyone: it is not your code.
        sys.exit("The model is saturated (429). Wait a minute, or "
                 "change MODELE in .env (python modele.py).")
