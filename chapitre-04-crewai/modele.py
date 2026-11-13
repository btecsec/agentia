"""The only door to a model in this book: OpenRouter.

OpenRouter speaks the OpenAI dialect: the `openai` SDK works as is,
only the base URL changes. The model is a slug read from MODELE.

    python modele.py    # free models that can call tools today
"""

import json
import os
import urllib.request

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # climbs up to the .env at the repository root

BASE_URL = "https://openrouter.ai/api/v1"
# Free (":free" costs nothing) and able to call tools.
DEFAULT_MODEL = "google/gemma-4-31b-it:free"
MODEL = os.environ.get("MODELE", DEFAULT_MODEL)
# When free quotas run out: a few cents for the whole book.
CHEAP_MODELS = ["deepseek/deepseek-v4-flash",
                "google/gemini-3.1-flash-lite"]


def get_client():
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise SystemExit("OPENROUTER_API_KEY is missing: copy "
                         ".env.example to .env and paste your key.")
    # Free models often answer 429 "busy": retry, waiting longer.
    return OpenAI(base_url=BASE_URL, api_key=key, max_retries=6)


def make_ask(client, model=MODEL):
    """A function messages -> text: the model, without the SDK."""
    def ask(messages):
        response = client.chat.completions.create(
            model=model, messages=messages)
        return response.choices[0].message.content or ""
    return ask


def free_models_with_tools():
    """Read the public catalogue: no key needed."""
    request = urllib.request.Request(
        f"{BASE_URL}/models", headers={"User-Agent": "mytravel"})
    with urllib.request.urlopen(request, timeout=15) as response:
        catalogue = json.load(response)["data"]
    return sorted(
        m["id"] for m in catalogue
        if m["id"].endswith(":free")
        and "tools" in (m.get("supported_parameters") or []))


def get_crew_llm():
    """The same OpenRouter model, seen through CrewAI.

    CrewAI has its own LLM class; the `openrouter/` prefix tells it
    where to go. Same key, same MODELE as chapter 1.
    """
    # Imported here: `python modele.py` must work without CrewAI.
    from crewai import LLM
    return LLM(model=f"openrouter/{MODEL}",
               api_key=get_client().api_key)


if __name__ == "__main__":
    print(f"Model in use: {MODEL}")
    print("Free models that can call tools today:")
    for slug in free_models_with_tools():
        print(" ", slug)
    print("Cheap fallback:", ", ".join(CHEAP_MODELS))
