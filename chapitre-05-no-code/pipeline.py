"""The same scenario as the n8n workflow, written in Python.

Search -> summarize -> email. Same boxes, same order. Reading both
side by side shows what a no-code platform gives you (a canvas,
connectors, credential screens) and what it hides (every line
below is yours to change).
"""

import json
import os
import smtplib
import urllib.parse
import urllib.request
from email.message import EmailMessage
from pathlib import Path

from modele import MODEL, get_client

WIKIPEDIA = "https://en.wikipedia.org/api/rest_v1/page/summary/"
USER_AGENT = "agentia-book/1.0 (github.com/btecsec)"


def fetch_summary(topic):
    """Box 1: search. The Wikipedia summary, or '' if none."""
    title = urllib.parse.quote(topic.strip().replace(" ", "_"))
    request = urllib.request.Request(
        WIKIPEDIA + title, headers={"User-Agent": USER_AGENT}
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as reply:
            return json.load(reply).get("extract") or ""
    except OSError:
        # No page, no network: the pipeline stops cleanly later.
        return ""


def summarize(text, client=None, model=MODEL):
    """Box 2: summarize with the model, in two sentences."""
    client = client or get_client()
    reply = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system",
             "content": "Summarize travel facts in 2 sentences."},
            {"role": "user", "content": text},
        ],
    )
    return reply.choices[0].message.content or ""


def build_email(subject, body, to, sender):
    """Box 3: build the email."""
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = to
    message.set_content(body)
    return message


def deliver(message, outbox=Path("outbox")):
    """Box 4: send through SMTP, or save an .eml file if none set.

    Saving a file is the safe default: a tutorial must never send
    a real email by surprise.
    """
    host = os.environ.get("SMTP_HOST")
    if host:
        port = int(os.environ.get("SMTP_PORT", 587))
        with smtplib.SMTP(host, port) as smtp:
            smtp.starttls()
            smtp.login(
                os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"]
            )
            smtp.send_message(message)
        return None
    outbox.mkdir(exist_ok=True)
    path = outbox / "summary.eml"
    path.write_bytes(bytes(message))
    return path


def run(topic, to="you@example.com", client=None,
        outbox=Path("outbox")):
    """The whole scenario. Returns the saved path, or None.

    The guard the n8n workflow draws as an IF box is one line here:
    nothing found, nothing sent.
    """
    research = fetch_summary(topic)
    if not research:
        return None
    summary = summarize(research, client=client)
    message = build_email(
        subject=f"Your summary: {topic}",
        body=summary,
        to=to,
        sender="mytravel@example.com",
    )
    return deliver(message, outbox=outbox)
