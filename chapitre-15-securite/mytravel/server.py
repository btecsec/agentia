"""myTravel's web server: the page, and the API the page calls.

    uvicorn server:app --reload     then open http://localhost:8000

Every request arrives here first. Read this file from top to
bottom: it is the map of the whole application.
"""

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from openai import APIError, RateLimitError
from pydantic import BaseModel, Field

from app.graph import stream_confirm, stream_mytravel
from app.guardrails import check_message
from app.security import (RateLimiter, add_security_headers,
                          claim, release, visitor)

PAGE = Path(__file__).parent / "static" / "index.html"

app = FastAPI(title="myTravel")
app.middleware("http")(add_security_headers)
limiter = RateLimiter(per_minute=10)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation: str = Field(min_length=8, max_length=64)


class Decision(BaseModel):
    conversation: str = Field(min_length=8, max_length=64)
    approved: bool


@app.get("/")
def page():
    return FileResponse(PAGE)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
def chat(body: ChatRequest, request: Request):
    if not limiter.allow(visitor(request)):
        raise HTTPException(429, "Trop de messages : attends une "
                                 "minute.")
    problem = check_message(body.message)
    if problem:  # refused before the model, and never saved
        return live([{"type": "done", "answer": problem,
                      "sources": [], "confirm": None}])
    claim(body.conversation)  # 409 now, before the stream starts
    events = stream_mytravel(body.message, body.conversation)
    return live(events, body.conversation)


@app.post("/api/confirm")
def confirm(body: Decision):
    claim(body.conversation)
    events = stream_confirm(body.conversation, body.approved)
    if events is None:
        release(body.conversation)
        raise HTTPException(404, "Aucune réservation en attente.")
    return live(events, body.conversation)


def live(events, conversation=""):
    """Each event sent as soon as it comes: a Server-Sent Event."""
    def lines():
        try:
            for event in events:
                yield sse(event)
        except Exception as error:  # the stream has started
            yield sse(failure(error))
        finally:
            release(conversation)
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
