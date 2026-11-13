"""Run chapter 4:  python main.py

Needs OPENROUTER_API_KEY in the .env file at the repository root,
and Python 3.13 or older (CrewAI does not support 3.14 yet).
"""

from crew import build_crew


def main():
    result = build_crew().kickoff(inputs={"city": "Lisbon"})

    # One output per task: we SEE what each role produced.
    for task_output in result.tasks_output:
        print(f"\n--- {task_output.agent} ---")
        print(task_output.raw)

    print("\n=== Final result ===")
    print(result.raw)


if __name__ == "__main__":
    main()
