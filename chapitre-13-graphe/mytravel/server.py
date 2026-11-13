"""myTravel's web server: the page, and the API the page calls.

    uvicorn server:app --reload     then open http://localhost:8000

Every request arrives here first. Read this file from top to
bottom: it is the map of the whole application.
"""

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from openai import APIError, RateLimitError
from pydantic import BaseModel, Field

from app.graph import stream_mytravel

PAGE = Path(__file__).parent / "static" / "index.html"

app = FastAPI(title="myTravel")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation: str = Field(min_length=8, max_length=64)


@app.get("/")
def page():
    return FileResponse(PAGE)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
def chat(body: ChatRequest):
    return live(stream_mytravel(body.message, body.conversation))


def live(events):
    """Each event sent as soon as it comes: a Server-Sent Event."""
    def lines():
        try:
            for event in events:
                yield sse(event)
        except Exception as error:  # the stream has started
            yield sse(failure(error))
    return StreamingResponse(lines(),
                             media_type="text/event-stream")


def sse(event):
    """One event: a "data:" line, then a blank line."""
    return f"data: {json.dumps(event)}\n\n"


def failure(error):
    """Too late for an HTTP error: the error is one more event."""
    if isinstance(error, RateLimitError):
        # Free quotas are shared by everyone: it is not your code.
        return {"type": "error", "detail": "Le modèle gratuit est "
                "saturé : réessaie dans une minute."}
    if isinstance(error, APIError):
        # The details stay in the server's terminal: they can
        # carry pieces of a key or of a prompt.
        print(f"Model error: {error}")
        return {"type": "error", "detail": "Erreur du modèle : "
                "regarde le terminal du serveur."}
    print(f"Server error: {error!r}")  # a bug
    return {"type": "error", "detail": "Erreur inattendue : "
            "regarde le terminal du serveur."}
