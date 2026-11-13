"""Run chapter 3:  python main.py

Needs OPENROUTER_API_KEY in the .env file at the repository root.
The state is saved in checkpoints.sqlite: the file stays on disk
after the script ends, so a later run can read the state back.
"""

import sys

from langgraph.checkpoint.sqlite import SqliteSaver
from openai import RateLimitError

from graph import build_graph, drawing

TOPIC = "why a travel assistant should check the weather"
DB_FILE = "checkpoints.sqlite"


def main():
    # The drawing needs no model: any placeholder will do.
    print(drawing(build_graph(model=object())))

    # SqliteSaver writes every step to disk: the state survives the
    # end of the program.
    with SqliteSaver.from_conn_string(DB_FILE) as saver:
        graph = build_graph(checkpointer=saver)
        config = {"configurable": {"thread_id": "essay-1"}}

        # stream() yields one update per node: we SEE the path.
        updates = graph.stream(
            {"topic": TOPIC}, config, stream_mode="updates"
        )
        for update in updates:
            for node, change in update.items():
                print(f"\n[{node}] {change}")

        final = graph.get_state(config).values
        count = final["revisions"]
        print(f"\nFinal draft after {count} revision(s):")
        print(final["draft"])


if __name__ == "__main__":
    try:
        main()
    except RateLimitError:
        # Free quotas are shared by everyone: it is not your code.
        sys.exit("The model is saturated (429). Wait a minute, or "
                 "change MODELE in .env (python modele.py).")
