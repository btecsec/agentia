"""Run chapter 5:  python main.py [topic]

Runs the Python version of the n8n scenario. The email is saved in
outbox/summary.eml unless SMTP_HOST is set.
"""

import sys

from openai import RateLimitError

from pipeline import run


def main():
    topic = sys.argv[1] if len(sys.argv) > 1 else "Lisbon"
    path = run(topic)
    if path is None:
        print(f"Nothing found for {topic!r}: no email produced.")
    else:
        print(f"Email saved in {path}")


if __name__ == "__main__":
    try:
        main()
    except RateLimitError:
        # Free quotas are shared by everyone: it is not your code.
        sys.exit("The model is saturated (429). Wait a minute, or "
                 "change MODELE in .env (python modele.py).")
