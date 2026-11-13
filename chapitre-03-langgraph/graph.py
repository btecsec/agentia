"""A write -> critique -> rewrite workflow as a LangGraph graph.

Chapter 2 gave a straight line: model, tools, model. Here the path
has a loop and a decision. A graph has three ingredients:

- a STATE: the bag every node passes around;
- NODES: Python functions that read the state and return what they
  want to change in it;
- EDGES: arrows saying which node runs after which. A CONDITIONAL
  edge picks its destination by looking at the state.

The graph:
  write -> critique -> approved? end : rewrite -> critique
"""

from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from modele import get_chat_model


class State(TypedDict):
    topic: str
    draft: str
    feedback: str
    revisions: int
    approved: bool


def parse_verdict(text):
    """Turn the critic's answer into (approved, feedback).

    We ask the model for 'APPROVED' or 'REVISE: <advice>'. Free text
    is easier for small models than JSON, and a plain parser is
    enough. Anything unclear counts as 'revise': safer than a false
    approval.
    """
    cleaned = text.strip()
    if cleaned.upper().startswith("APPROVED"):
        return True, ""
    feedback = cleaned.split(":", 1)[-1].strip()
    return False, feedback or "Improve clarity."


def route_after_critique(state, max_revisions=2):
    """The conditional edge: where do we go after the critic?"""
    if state["approved"]:
        return END
    if state["revisions"] >= max_revisions:
        return END  # the safety net, visible on the drawing
    return "rewrite"


def build_graph(model=None, max_revisions=2, checkpointer=None,
                review=False):
    """Assemble and compile the graph. Tests inject a `model`."""
    model = model or get_chat_model()

    def write(state: State):
        prompt = (
            "Write a paragraph of three sentences about: "
            f"{state['topic']}"
        )
        draft = model.invoke(prompt).content
        return {"draft": draft, "revisions": 0}

    def critique(state: State):
        prompt = (
            "You are a strict editor. Read this paragraph.\n"
            "Answer 'APPROVED' only if it contains at least one "
            "concrete figure (a number, a date or a percentage). "
            "Otherwise answer 'REVISE: ' followed by one sentence "
            f"of advice.\n\nParagraph:\n{state['draft']}"
        )
        verdict = model.invoke(prompt).content
        approved, feedback = parse_verdict(verdict)
        return {"approved": approved, "feedback": feedback}

    def rewrite(state: State):
        prompt = (
            "Rewrite this paragraph, applying the advice.\n"
            f"Advice: {state['feedback']}\n\n"
            f"Paragraph:\n{state['draft']}"
        )
        return {
            "draft": model.invoke(prompt).content,
            "revisions": state["revisions"] + 1,
        }

    graph = StateGraph(State)
    graph.add_node("write", write)
    graph.add_node("critique", critique)
    graph.add_node("rewrite", rewrite)
    graph.add_edge(START, "write")
    graph.add_edge("write", "critique")
    graph.add_conditional_edges(
        "critique",
        lambda state: route_after_critique(state, max_revisions),
        ["rewrite", END],
    )
    graph.add_edge("rewrite", "critique")
    return graph.compile(
        checkpointer=checkpointer or InMemorySaver(),
        # Pause before each rewrite so a human can read the advice.
        interrupt_before=["rewrite"] if review else None,
    )


def drawing(graph):
    """The graph as Mermaid text, for any Mermaid viewer."""
    return graph.get_graph().draw_mermaid()
