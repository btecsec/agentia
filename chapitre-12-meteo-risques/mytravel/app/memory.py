"""What myTravel remembers, in one SQLite file.

The conversation: every message, saved by LangGraph after each
step (the "checkpointer"), found again by conversation id. What
the traveler said about themselves (nationality, home city,
budget) is in those messages: the model reads it there.
"""

import os
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver

DB = os.environ.get("MYTRAVEL_DB", "mytravel.db")
# FastAPI answers in several threads: allow them to share the
# connection, one query at a time (SqliteSaver locks it).
saver_db = sqlite3.connect(DB, check_same_thread=False)


def checkpointer():
    return SqliteSaver(saver_db)
