"""Checks before the model reads, and after it writes.

On the way in: a card number never enters the conversation.
On the way out: a link is kept only if a tool returned it, and
only to a site we trust, whatever the model believes.
"""

import html
import re

from app.sources import GOOGLE_FLIGHTS, TRUSTED
from app.web import is_allowed

# 13 digits or more, spaces or dashes allowed.
CARD = re.compile(r"\b(?:\d[ -]?){12,}\d\b")
DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")  # 2027-05-02
# [words](target "title"): any target, checked below.
LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)[^)]*\)")
# Anything a browser would open: https://x, HTTP://x, //x, www.x
# It ends before "]", « », and the punctuation of other scripts:
# some models cite as 【https://x】.
END = (r"\s<>()\]\"'\u00ab\u00bb"
       r"\u2000-\u206f\u3000-\u303f\uff00-\uffef")
URL = re.compile(rf"(?:https?:)?//[^{END}]+|www\.[^{END}]+",
                 re.IGNORECASE)
# What ends a sentence or wraps a link in Markdown (**x**, x:)
# is not part of it: the page would not open it either.
TAIL = ".,;:!?*_~"
# Raw HTML: the model has no reason to write any, and a browser
# decodes what a regex cannot see (&#104;ttps://...).
HTML_TAG = re.compile(r"</?[a-zA-Z][^>]*>")
# A Markdown link or a lone URL, in one pass from left to right:
# the URL inside [words](target) is never read twice.
TOKEN = re.compile(f"{LINK.pattern}|{URL.pattern}", re.IGNORECASE)


def passes_luhn(number):
    """The checksum every real card number passes.

    From the right, double every second digit (minus 9 above 9);
    the total of all digits ends with 0.
    """
    digits = [int(c) for c in number if c.isdigit()]
    total = 0
    for position, digit in enumerate(reversed(digits)):
        if position % 2 == 1:
            digit = digit * 2 - 9 if digit > 4 else digit * 2
        total += digit
    return total % 10 == 0


def has_card_number(text):
    text = DATE.sub(" ", text)  # two dates are not a card
    for match in CARD.finditer(text):
        digits = [c for c in match.group() if c.isdigit()]
        # A card hidden in a longer run of digits still counts.
        for size in range(13, 20):
            for start in range(len(digits) - size + 1):
                if passes_luhn(digits[start:start + size]):
                    return True
    return False


def check_message(text):
    """None if the message may go on, else why it may not."""
    if has_card_number(text):
        return ("Ne m'envoie jamais un numéro de carte : myTravel "
                "ne paie rien. Tu réserves toi-même sur le site du "
                "fournisseur. Ton message n'a pas été enregistré.")
    return None


def full(url):
    """//x and www.x are links too: give them their https."""
    if url.startswith("//"):
        return "https:" + url
    if url.lower().startswith("www."):
        return "https://" + url
    return url


def link_of(raw):
    """(the URL a browser opens, the punctuation after it)."""
    url = raw.rstrip(TAIL)
    return full(url), raw[len(url):]


def links_in(text):
    """Every URL in a tool result, as clean_answer will see it."""
    return [link_of(match.group(0))[0]
            for match in URL.finditer(html.unescape(text))]


def trusted(url):
    if url.startswith(GOOGLE_FLIGHTS):
        return True
    return is_allowed(url, TRUSTED)


def clean_answer(text, found):
    """(text without the bad links, the links kept)."""
    sources = []

    # found: what the tools returned. Anything else is made up.
    def kept(url):
        if url in found and trusted(url):
            sources.append(url)
            return True
        return False

    def keep(match):
        label, target = match.group(1), match.group(2)
        if target is not None:  # [label](target)
            if kept(full(target)):  # rebuilt: nothing hides after
                return f"[{TOKEN.sub(keep, label)}]({full(target)})"
            return TOKEN.sub(keep, label)  # the words stay
        url, tail = link_of(match.group(0))
        if kept(url):  # <url>: the page opens exactly this one
            return f"<{url}>{tail}"
        return "[lien retiré]" + tail

    # Decoded first, as the browser will: &#104;ttps is https.
    # Again until nothing moves: &amp;#104; hides one more turn.
    while (clean := HTML_TAG.sub("", html.unescape(text))) != text:
        text = clean
    return TOKEN.sub(keep, text), list(dict.fromkeys(sources))
