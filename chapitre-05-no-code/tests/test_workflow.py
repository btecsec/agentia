"""Chapter 5 tests: the n8n workflow file, and its Python twin.

No key, no network, no n8n needed. We check the workflow like any
other file of the project: it is JSON, so it can be tested.
"""

import json
import sys
from email import message_from_bytes
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pipeline  # noqa: E402

WORKFLOW = ROOT / "workflows" / "research-summary-email.n8n.json"


@pytest.fixture(scope="module")
def workflow():
    return json.loads(WORKFLOW.read_text(encoding="utf-8"))


def nodes_by_type(workflow, node_type):
    return [n for n in workflow["nodes"] if n["type"] == node_type]


# --- the workflow file ---------------------------------------------------


def test_workflow_is_valid_json_with_the_four_n8n_keys(workflow):
    assert {"name", "nodes", "connections"} <= set(workflow)


def test_node_names_are_unique(workflow):
    names = [n["name"] for n in workflow["nodes"]]
    assert len(names) == len(set(names))


def test_every_connection_points_to_an_existing_node(workflow):
    names = {n["name"] for n in workflow["nodes"]}
    for source, outputs in workflow["connections"].items():
        assert source in names
        for branch in outputs["main"]:
            for link in branch:
                assert link["node"] in names


def test_it_starts_with_a_trigger(workflow):
    assert len(nodes_by_type(workflow, "n8n-nodes-base.manualTrigger")) == 1


def test_the_chain_runs_search_then_model_then_email(workflow):
    def follow(name):
        branches = workflow["connections"].get(name, {"main": []})["main"]
        return [link["node"] for b in branches for link in b]

    path, current = [], "Manual Trigger"
    while current:
        path.append(current)
        # On the IF node, follow the 'true' branch (output 0).
        current = (follow(current) or [None])[0]

    assert path == [
        "Manual Trigger", "Set Topic", "Search Wikipedia",
        "Found Something?", "Summarize with OpenRouter", "Send Email",
    ]


def test_the_if_node_guards_the_model_call(workflow):
    # 'false' branch (output 1): empty, nothing is sent.
    branches = workflow["connections"]["Found Something?"]["main"]
    assert branches[0] and branches[1] == []


def test_the_model_goes_through_openrouter_with_a_free_slug(workflow):
    call = next(
        n for n in workflow["nodes"]
        if n["name"] == "Summarize with OpenRouter"
    )
    assert call["parameters"]["url"].startswith("https://openrouter.ai/")
    assert ":free" in call["parameters"]["jsonBody"]


def test_no_secret_is_written_in_the_file(workflow):
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "sk-or-" not in text
    # Credentials are references to be filled in n8n, never values.
    for node in workflow["nodes"]:
        for ref in node.get("credentials", {}).values():
            assert ref["id"] == "REPLACE_ME"


# --- the Python twin ---------------------------------------------------------


class FakeClient:
    """Minimal stand-in for the OpenRouter client."""

    def __init__(self, text):
        self.requests = []
        reply = SimpleNamespace(
            choices=[SimpleNamespace(
                message=SimpleNamespace(content=text))]
        )
        self.chat = SimpleNamespace(completions=SimpleNamespace(
            create=lambda **kw: (self.requests.append(kw), reply)[1]
        ))


def test_summarize_sends_the_research_to_the_model():
    client = FakeClient("Short summary.")
    assert pipeline.summarize("long text", client=client) == "Short summary."
    assert client.requests[0]["messages"][-1]["content"] == "long text"


def test_build_email_sets_headers_and_body():
    mail = pipeline.build_email("Hi", "Body", "a@x.org", "b@x.org")
    assert (mail["Subject"], mail["To"], mail["From"]) == (
        "Hi", "a@x.org", "b@x.org"
    )
    assert mail.get_content().strip() == "Body"


def test_run_saves_an_eml_file_by_default(tmp_path, monkeypatch):
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.setattr(pipeline, "fetch_summary", lambda t: "Facts.")
    path = pipeline.run(
        "Lisbon", client=FakeClient("Two sentences."), outbox=tmp_path
    )

    mail = message_from_bytes(path.read_bytes())
    assert mail["Subject"] == "Your summary: Lisbon"
    assert "Two sentences." in mail.get_payload()


def test_run_sends_nothing_when_nothing_is_found(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "fetch_summary", lambda t: "")
    client = FakeClient("never used")

    assert pipeline.run("Xyzzy", client=client, outbox=tmp_path) is None
    assert client.requests == []  # the model was not even called
    assert list(tmp_path.iterdir()) == []
