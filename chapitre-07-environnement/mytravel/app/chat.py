"""myTravel's first answer: one message in, words out.

No memory yet, no tools yet: the point is to prove the whole
chain works, page -> server -> OpenRouter -> model -> page,
and that the answer shows word by word, as the model writes it.
"""

from app.modele import get_chat_model

PROMPT = """You are myTravel, a travel assistant. You find and
compare offers; the traveler books and pays on the provider's
website. Answer in the traveler's language, in a few lines."""


def stream_mytravel(message):
    """Each piece of the answer as soon as the model writes it."""
    answer = ""
    for chunk in get_chat_model().stream(
            [("system", PROMPT), ("user", message)]):
        if chunk.content:  # some chunks carry no text
            answer += chunk.content
            yield {"type": "token", "text": chunk.content}
    yield {"type": "done", "answer": answer}
