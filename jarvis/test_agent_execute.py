"""Test explicit confirmation for agent actions.

Run:
    python -m jarvis.test_agent_execute
"""

from jarvis.agent import AgentPlanner
from jarvis.agent.executor import ToolExecutor
from jarvis.config import load_config


def run_plan(executor, plan):
    for step in plan.steps:
        result = executor.run_step(step)
        print(" ", result.pretty())

        if result.status == "needs_confirmation":
            response = input("\nConfirmation: ").strip()

            if not response.startswith("confirm "):
                print("  Confirmation declined. Plan stopped.")
                return

            token = response.removeprefix("confirm ").strip()
            result = executor.run_step(step, confirmation_token=token)
            print(" ", result.pretty())

        if result.status != "succeeded":
            print("  Plan stopped.")
            return

        if not result.verified:
            print("  Plan stopped because the result was not verified.")
            return


def main():
    cfg = load_config()

    if cfg["brain"]["engine"] != "groq":
        print("Set brain.engine to 'groq' in config.yaml before testing.")
        return

    if not cfg["agent"]["execution"]["allow_low_risk"]:
        print(
            "Execution is disabled. Temporarily set "
            "agent.execution.allow_low_risk to true for testing."
        )
        return

    planner = AgentPlanner(cfg)
    executor = ToolExecutor(cfg)

    print("Jarvis confirmed-action executor")
    print("Every plan requires 'execute'; confirm-risk steps require a second token.")
    print("Type q to quit.")

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

            if plan.mode != "plan":
                continue

            decision = input("\nType execute to start this plan: ").strip().lower()
            if decision != "execute":
                print("Skipped. No action was executed.")
                continue

            print("\nExecution results:")
            run_plan(executor, plan)

        except Exception as error:
            print(f"\nAgent error: {error}")


if __name__ == "__main__":
    main()