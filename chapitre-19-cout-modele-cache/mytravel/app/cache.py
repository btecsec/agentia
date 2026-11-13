"""Remember web searches for a day.

The same question about Japan, asked ten times in an hour, costs
one search instead of ten. Visa rules do not change by the hour.
"""

import json
import os
import sqlite3
import threading
import time

DB = os.environ.get("MYTRAVEL_DB", "mytravel.db")
connection = sqlite3.connect(DB, check_same_thread=False)
lock = threading.Lock()  # parallel agents search at the same time
connection.execute("CREATE TABLE IF NOT EXISTS cache "
                   "(key TEXT PRIMARY KEY, saved REAL, value TEXT)")


def get(key, max_age_hours=24):
    with lock:
        row = connection.execute(
            "SELECT saved, value FROM cache WHERE key = ?",
            (key,)).fetchone()
    if row and time.time() - row[0] < max_age_hours * 3600:
        return json.loads(row[1])
    return None


def put(key, value):
    with lock, connection:  # one at a time, committed
        connection.execute(
            "INSERT OR REPLACE INTO cache VALUES (?, ?, ?)",
            (key, time.time(), json.dumps(value)))
