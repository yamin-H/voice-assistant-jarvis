"""Test Jarvis agent planning without voice or computer control.

Run:
    python -m jarvis.test_agent

This tool never opens apps, types, searches, or performs any action.
"""

from jarvis.agent import AgentPlanner
from jarvis.config import load_config


def main():
    cfg = load_config()

    if cfg["brain"]["engine"] != "groq":
        print("Set brain.engine to 'groq' in config.yaml before testing the planner.")
        return

    planner = AgentPlanner(cfg)

    print("Jarvis dry-run planner")
    print("No plan will be executed. Type q to quit.")

    while True:
        request = input("\nYou: ").strip()

        if request.lower() in {"q", "quit", "exit"}:
            break

        if not request:
            continue

        try:
            plan = planner.plan(request)
            print()
            print(plan.pretty())
        except Exception as error:
            print(f"\nPlanner error: {error}")


if __name__ == "__main__":
    main()