"""Defences of a public web app that reads the web.

Two threats: a page that hides orders for the model (prompt
injection), and a visitor who sends a thousand messages a minute.
"""

import html
import os
import re
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException

# Sentences written for a model, not for a traveler.
SUSPICIOUS = re.compile(
    r"(ignore|disregard|forget)\b.{0,30}\b(instructions|rules)"
    r"|system prompt|you are now|tu es maintenant",
    re.IGNORECASE)
# Our own tags, in any case or spacing: no way out of the box.
TAG = re.compile(r"<\s*/?\s*untrusted[^>]*>", re.IGNORECASE)


def untrusted(text, url):
    """Wrap web content so the model reads it as data."""
    text = TAG.sub("[removed]", text)
    text = SUSPICIOUS.sub("[removed]", text)
    url = html.escape(url)  # nor can a strange URL
    return f'<untrusted source="{url}">\n{text}\n</untrusted>'


def visitor(request):
    """The visitor's address, as seen by the rate limiter.

    Behind Cloud Run, request.client is Google's front end. The
    real address is the last one of X-Forwarded-For: Google adds
    it, while the ones before come from the visitor and can lie.
    Anywhere else, anyone can write that header: ignore it.
    Cloud Run sets K_SERVICE in every container it starts.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded and os.environ.get("K_SERVICE"):
        return forwarded.split(",")[-1].strip()
    return request.client.host


working = set()  # conversations being answered right now
working_lock = threading.Lock()


def claim(conversation):
    """Refuse a second message while the first is answered.

    Two answers on one conversation would start from the same
    memory, and the last to finish would erase the other.
    """
    with working_lock:
        if conversation in working:
            raise HTTPException(409, "Une réponse est déjà en "
                                     "cours : patiente.")
        working.add(conversation)


def release(conversation):
    """The answer is sent, or failed: the next one may come."""
    with working_lock:
        working.discard(conversation)


class RateLimiter:
    """At most `per_minute` messages per visitor (per IP)."""

    def __init__(self, per_minute=10):
        self.per_minute = per_minute
        self.seen = defaultdict(deque)  # ip -> recent times
        self.lock = threading.Lock()  # requests run in threads

    def allow(self, ip):
        now = time.monotonic()
        with self.lock:
            # Forget visitors silent for a minute: the table stays
            # as small as the number of recent visitors.
            for old in [k for k, t in self.seen.items()
                        if now - t[-1] > 60]:
                del self.seen[old]
            times = self.seen[ip]
            while times and now - times[0] > 60:
                times.popleft()
            if len(times) >= self.per_minute:
                return False
            times.append(now)
            return True


# The page may load its scripts from cdnjs only, and talk to its
# own server only: injected HTML cannot call anywhere else.
POLICY = ("default-src 'self'; "
          "script-src 'self' 'unsafe-inline' "
          "https://cdnjs.cloudflare.com; "
          "style-src 'self' 'unsafe-inline' "
          "https://fonts.googleapis.com; "
          "font-src https://fonts.gstatic.com; "
          "img-src 'self' data:; connect-src 'self'")


async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = POLICY
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response
