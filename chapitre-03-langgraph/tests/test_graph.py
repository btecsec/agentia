"""Chapter 3 tests: no key, no network (a scripted model)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from langgraph.checkpoint.sqlite import SqliteSaver  # noqa: E402
from langgraph.graph import END  # noqa: E402

from fake_model import ScriptedModel  # noqa: E402
from graph import (  # noqa: E402
    build_graph,
    drawing,
    parse_verdict,
    route_after_critique,
)

CONFIG = {"configurable": {"thread_id": "t1"}}


def run(model, **options):
    graph = build_graph(model=model, **options)
    return graph, graph.invoke({"topic": "Lisbon"}, CONFIG)


# --- pure functions -----------------------------------------------------


def test_parse_verdict_approved():
    assert parse_verdict("APPROVED") == (True, "")
    assert parse_verdict("  approved, nice work") == (True, "")


def test_parse_verdict_revise_keeps_the_advice():
    assert parse_verdict("REVISE: add a number") == (False, "add a number")


def test_parse_verdict_unclear_means_revise():
    approved, feedback = parse_verdict("hmm, maybe")
    assert approved is False and feedback


def test_route_ends_when_approved():
    state = {"approved": True, "revisions": 0}
    assert route_after_critique(state) == END


def test_route_rewrites_when_not_approved():
    state = {"approved": False, "revisions": 1}
    assert route_after_critique(state, max_revisions=2) == "rewrite"


def test_route_stops_at_the_revision_limit():
    state = {"approved": False, "revisions": 2}
    assert route_after_critique(state, max_revisions=2) == END


# --- the graph ----------------------------------------------------------


def test_approved_first_time_takes_two_calls():
    model = ScriptedModel("Draft one.", "APPROVED")
    _, result = run(model)

    assert model.calls == 2
    assert result["draft"] == "Draft one."
    assert result["revisions"] == 0 and result["approved"] is True


def test_one_revision_takes_four_calls():
    model = ScriptedModel(
        "Draft one.", "REVISE: add a number", "Draft two.", "APPROVED"
    )
    _, result = run(model)

    assert model.calls == 4
    assert result["draft"] == "Draft two."
    assert result["revisions"] == 1
    # The rewrite node received the critic's advice.
    assert "add a number" in model.prompts[2]


def test_a_never_satisfied_critic_cannot_loop_forever():
    answers = ["Draft"] + ["REVISE: more", "Draft again"] * 2
    model = ScriptedModel(*answers, "REVISE: still more")
    _, result = run(model, max_revisions=2)

    assert result["revisions"] == 2
    assert result["approved"] is False
    assert model.calls == 6  # write + 2 x (critique, rewrite) + critique


def test_drawing_lists_every_node():
    graph = build_graph(model=ScriptedModel())
    mermaid = drawing(graph)
    for node in ("write", "critique", "rewrite"):
        assert node in mermaid


# --- checkpointing ------------------------------------------------------


def test_state_is_saved_in_the_checkpointer():
    graph, _ = run(ScriptedModel("Draft one.", "APPROVED"))
    snapshot = graph.get_state(CONFIG)

    assert snapshot.values["draft"] == "Draft one."
    assert snapshot.next == ()  # nothing left to run


def test_pause_before_rewrite_then_resume():
    model = ScriptedModel(
        "Draft one.", "REVISE: shorter", "Draft two.", "APPROVED"
    )
    graph, paused = run(model, review=True)

    # The graph stopped BEFORE the rewrite node: a human can step in.
    assert graph.get_state(CONFIG).next == ("rewrite",)
    assert paused["draft"] == "Draft one."

    graph.invoke(None, CONFIG)  # None = "continue where you stopped"
    assert graph.get_state(CONFIG).values["draft"] == "Draft two."


def test_state_survives_a_restart_on_disk(tmp_path):
    db = str(tmp_path / "checkpoints.sqlite")
    with SqliteSaver.from_conn_string(db) as saver:
        run(ScriptedModel("Saved draft.", "APPROVED"), checkpointer=saver)

    # A brand new saver, a brand new graph: same file, same thread.
    with SqliteSaver.from_conn_string(db) as saver:
        graph = build_graph(model=ScriptedModel(), checkpointer=saver)
        assert graph.get_state(CONFIG).values["draft"] == "Saved draft."
