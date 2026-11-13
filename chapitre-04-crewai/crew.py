"""A content team with CrewAI: researcher, writer, reviewer.

CrewAI thinks in ROLES, not in graphs:

- an AGENT is a character: a role, a goal, a backstory;
- a TASK is a job: a description and the expected output;
- a CREW is the team: who does which task, in which process.

Nothing here says "go to node X then Y". The order comes from the
process (sequential) and from each task's `context`, i.e. which
earlier results it receives.
"""

from crewai import Agent, Crew, Process, Task
from crewai.tools import tool

from modele import get_crew_llm

# The "web" of this chapter: a few facts, the same every run.
FACTS = {
    "lisbon": "550,000 inhabitants; trams on steep hills; "
              "pasteis de nata; 290 sunny days a year.",
    "kyoto": "1.4 million inhabitants; over 1,600 temples; "
             "imperial capital until 1868.",
}


@tool("Look up a city")
def lookup_city(city: str) -> str:
    """Return verified facts about a city (Lisbon, Kyoto)."""
    facts = FACTS.get(city.strip().lower())
    return facts or f"No facts for {city!r}."


def build_crew(llm=None, hierarchical=False):
    """Assemble the team. Tests inject a fake `llm`."""
    llm = llm or get_crew_llm()

    researcher = Agent(
        role="Travel Researcher",
        goal="Collect accurate facts about {city}",
        backstory="You are a meticulous researcher. You never "
                  "state a fact you did not get from your tool.",
        tools=[lookup_city],
        llm=llm,
    )
    writer = Agent(
        role="Travel Writer",
        goal="Write a vivid paragraph about {city}",
        backstory="You write for a travel magazine: short "
                  "sentences, concrete details, no cliches.",
        llm=llm,
    )
    reviewer = Agent(
        role="Fact Checker",
        goal="Make sure every claim comes from the research",
        backstory="You are an editor who deletes anything the "
                  "research does not support.",
        llm=llm,
    )

    research = Task(
        description="Find the key facts about {city}.",
        expected_output="A bullet list of 3 to 5 facts.",
        agent=researcher,
    )
    writing = Task(
        description="Write a paragraph of 3 sentences about {city} "
                    "using the research.",
        expected_output="One paragraph of 3 sentences.",
        agent=writer,
        context=[research],  # the writer receives the facts
    )
    review = Task(
        description="Check the paragraph against the research and "
                    "return the corrected final version.",
        expected_output="The final paragraph, nothing else.",
        agent=reviewer,
        context=[research, writing],
    )

    if hierarchical:
        # A manager agent decides who does what, instead of a fixed
        # order. It needs its own model.
        options = {
            "process": Process.hierarchical,
            "manager_llm": llm,
        }
    else:
        options = {"process": Process.sequential}

    return Crew(
        agents=[researcher, writer, reviewer],
        tasks=[research, writing, review],
        verbose=False,
        **options,
    )
