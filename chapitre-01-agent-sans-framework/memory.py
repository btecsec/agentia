"""Keeping the conversation inside the context window.

The model reads the WHOLE message list at every turn, and that
list has a size limit (the context window). Past it, the request
fails or old messages are silently dropped. Here we cut on
purpose, cleanly.
"""


def estimate_tokens(messages):
    """Rough size of the conversation, in tokens.

    A token is a chunk of a word: about four characters in
    English. An estimate is enough to decide when to trim.
    """
    chars = sum(len(str(m.get("content") or "")) for m in messages)
    return chars // 4


def trim_messages(messages, max_messages):
    """Keep the system prompt and the most recent messages.

    The cut always lands on a `user` message. Cutting between a
    tool request and its result leaves an orphan `tool` message,
    and the API rejects it.
    """
    if len(messages) <= max_messages:
        return messages

    system, rest = messages[0], messages[1:]
    start = len(rest) - (max_messages - 1)
    # Move the cut forward to the next user message.
    while start < len(rest) and rest[start]["role"] != "user":
        start += 1
    return [system, *rest[start:]]
