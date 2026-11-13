"""The only door to a model in myTravel: OpenRouter.

OpenRouter speaks the OpenAI dialect, so LangChain's ChatOpenAI
works as is: only the base URL changes. The model is a slug read
from MODELE in the .env file.

    python -m app.modele    # free models that can call tools today
"""

import json
import os
import urllib.request

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.config import get_config

load_dotenv()  # climbs up to the .env at the repository root

BASE_URL = "https://openrouter.ai/api/v1"
# Free (":free" costs nothing) and able to call tools.
DEFAULT_MODEL = "google/gemma-4-31b-it:free"
MODEL = os.environ.get("MODELE", DEFAULT_MODEL)
# If a model is busy, OpenRouter tries the next one by itself.
# Not "openrouter/free": it may pick a model that only grades
# messages and answers "User Safety: safe".
FREE_BACKUPS = ["google/gemma-4-26b-a4b-it:free",
                "nvidia/nemotron-3-ultra-550b-a55b:free"]
# Chapter 19: the specialist agents can run on a cheaper model.
FAST_MODEL = os.environ.get("MODELE_RAPIDE", MODEL)
# Chapter 19: a few cents a question when every free model is
# busy, and only once the traveler said yes (see server.py).
PAID_MODEL = os.environ.get("MODELE_PAYANT",
                            "deepseek/deepseek-v4-flash")


def paid():
    """True in a graph run the traveler agreed to pay for."""
    try:
        return get_config()["configurable"].get("paid", False)
    except RuntimeError:  # outside a graph: never
        return False


def get_chat_model(model=MODEL):
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is missing: copy "
                           ".env.example to .env, paste your key.")
    if paid():
        model = PAID_MODEL
    # "models": OpenRouter's own fallback list, tried in order
    # when a model answers 429 "busy". Then we retry twice.
    backups = [name for name in FREE_BACKUPS if name != model]
    return ChatOpenAI(model=model, base_url=BASE_URL, api_key=key,
                      temperature=0, max_retries=2,
                      extra_body={"models": [model, *backups]})


if __name__ == "__main__":
    # The public catalogue: no key needed. Slugs change every few
    # months, so the book asks OpenRouter instead of guessing.
    request = urllib.request.Request(
        f"{BASE_URL}/models", headers={"User-Agent": "mytravel"})
    with urllib.request.urlopen(request, timeout=15) as response:
        catalogue = json.load(response)["data"]
    print(f"Model in use: {MODEL}")
    print("Free models that can call tools today:")
    for model in catalogue:
        tools = "tools" in (model.get("supported_parameters") or [])
        if model["id"].endswith(":free") and tools:
            print(" ", model["id"])
