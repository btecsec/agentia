"""Chapter 4 tests: no key, no network (a scripted model).

CrewAI needs Python 3.13 or older. On 3.14 these tests are skipped,
not failed: see the chapter README.
"""

import sys
from pathlib import Path

import pytest

pytest.importorskip("crewai", reason="CrewAI needs Python <= 3.13")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from crewai import Process  # noqa: E402

from crew import FACTS, build_crew, lookup_city  # noqa: E402
from fake_llm import ScriptedLLM, final  # noqa: E402

# CrewAI itself raises deprecation warnings that bury ours.
pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def scripted_run(*answers, **options):
    llm = ScriptedLLM(*answers)
    crew = build_crew(llm=llm, **options)
    return llm, crew, crew.kickoff(inputs={"city": "Lisbon"})


# --- the team is what we declared ---------------------------------------


def test_three_roles_each_with_a_goal_and_a_backstory():
    crew = build_crew(llm=ScriptedLLM())
    roles = [a.role for a in crew.agents]

    assert roles == ["Travel Researcher", "Travel Writer", "Fact Checker"]
    assert all(a.goal and a.backstory for a in crew.agents)


def test_tasks_follow_the_roles_in_order():
    crew = build_crew(llm=ScriptedLLM())
    assert [t.agent.role for t in crew.tasks] == [
        "Travel Researcher", "Travel Writer", "Fact Checker"
    ]


def test_each_task_receives_the_results_it_needs():
    research, writing, review = build_crew(llm=ScriptedLLM()).tasks

    # No `context` given: CrewAI keeps a NOT_SPECIFIED marker.
    assert not isinstance(research.context, list)
    assert writing.context == [research]
    assert review.context == [research, writing]


def test_default_process_is_sequential():
    assert build_crew(llm=ScriptedLLM()).process == Process.sequential


def test_hierarchical_process_needs_a_manager_model():
    crew = build_crew(llm=ScriptedLLM(), hierarchical=True)
    assert crew.process == Process.hierarchical
    assert crew.manager_llm is not None


# --- the tool ------------------------------------------------------------


def test_lookup_tool_returns_known_facts():
    assert "trams" in lookup_city.run(city="Lisbon")


def test_lookup_tool_unknown_city_is_a_sentence():
    assert "No facts" in lookup_city.run(city="Atlantis")


def test_researcher_owns_the_tool_and_others_do_not():
    researcher, writer, reviewer = build_crew(llm=ScriptedLLM()).agents
    assert [t.name for t in researcher.tools] == ["Look up a city"]
    assert not writer.tools and not reviewer.tools


# --- a full run with a scripted model ----------------------------------------


def test_final_result_is_the_last_task_output():
    _, _, result = scripted_run(
        final("FACTS"), final("DRAFT"), final("REVIEWED")
    )
    assert result.raw == "REVIEWED"
    assert [o.raw for o in result.tasks_output] == [
        "FACTS", "DRAFT", "REVIEWED"
    ]


def test_inputs_fill_the_placeholders():
    llm, _, _ = scripted_run(final("a"), final("b"), final("c"))
    assert "Lisbon" in llm.prompt_text(0)
    assert "{city}" not in llm.prompt_text(0)


def test_the_writer_sees_the_research_and_not_the_other_way():
    llm, _, _ = scripted_run(
        final("RESEARCH-RESULT"), final("DRAFT-RESULT"), final("x")
    )
    assert "RESEARCH-RESULT" in llm.prompt_text(1)  # writer
    assert "DRAFT-RESULT" not in llm.prompt_text(0)  # researcher
    assert "DRAFT-RESULT" in llm.prompt_text(2)  # reviewer


def test_sequential_crew_always_makes_three_model_calls():
    # Like the linear pipeline of chapter 3: the shape of the work
    # does not depend on the content. No loop, no early exit.
    llm, _, _ = scripted_run(final("a"), final("b"), final("c"))
    assert len(llm.prompts) == 3


def test_facts_are_available_to_the_tool():
    assert set(FACTS) == {"lisbon", "kyoto"}
