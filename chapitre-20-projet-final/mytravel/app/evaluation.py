"""Checks a machine can run on a real answer.

A case says what a good answer must contain: the agents that
worked, the official sites it cites, the words it must say. The
checks are dumb on purpose: they never disagree with themselves.
"""


def check_case(case, reply):
    """The list of problems of one reply. Empty means passed."""
    problems = []
    called = {step.split(" (")[0] for step in reply["steps"]}
    missing = set(case.get("agents", [])) - called
    if missing:
        problems.append(f"agents not called: {sorted(missing)}")
    for site in case.get("must_cite", []):
        if not any(site in url for url in reply["sources"]):
            problems.append(f"no source from {site}")
    answer = reply["answer"].lower()
    for word in case.get("must_say", []):
        if word.lower() not in answer:
            problems.append(f"does not say {word!r}")
    return problems
