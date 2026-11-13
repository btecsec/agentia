"""Run the evaluation cases against the real agents.

    python evaluate.py      # needs OPENROUTER_API_KEY, uses quota

Each case is a fresh conversation, so the cases do not see each
other. The score goes up when you improve a prompt: that is the
point of measuring.
"""

import json
import uuid
from pathlib import Path

from app.evaluation import check_case
from app.graph import ask_mytravel

CASES = Path(__file__).parent / "data" / "eval_cases.json"


def main():
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    passed = 0
    for case in cases:
        conversation = uuid.uuid4().hex
        reply = ask_mytravel(case["question"], conversation)
        problems = check_case(case, reply)
        passed += not problems
        print("PASS" if not problems else "FAIL", case["question"])
        for problem in problems:
            print("     -", problem)
    print(f"\n{passed}/{len(cases)} cases passed")


if __name__ == "__main__":
    main()
