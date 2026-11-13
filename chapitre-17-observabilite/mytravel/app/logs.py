"""One JSON line per event, on the standard output.

On your machine, you read them in the terminal. On Cloud Run, the
same lines become searchable logs: "severity" is the field Google
reads to colour them.
"""

import json
from datetime import datetime, timezone


def log(event, **fields):
    line = {"time": datetime.now(timezone.utc).isoformat(),
            "severity": "INFO", "event": event, **fields}
    print(json.dumps(line, ensure_ascii=False, default=str),
          flush=True)
