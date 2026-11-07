"""Test grounded, step-by-step public web browsing.

Run:
    python -m jarvis.test_browser_agent

Every browser navigation needs explicit terminal approval.
"""

from jarvis.browser import BrowserAgent, BrowserSession
from jarvis.config import load_config


def execute_action(browser, action):
    if action.kind == "search":
        return browser.search(action.query)

    if action.kind == "open_url":
        return browser.open_url(action.url)

    if action.kind == "follow_link":
        return browser.follow_link(action.link_index)

    raise ValueError(f"Action '{action.kind}' cannot be executed.")


def main():
    cfg = load_config()

    browser = BrowserSession(cfg)
    agent = BrowserAgent(cfg)
    max_actions = cfg["browser"]["agent_max_actions"]

    print("Starting grounded Jarvis Browser...")
    print("Only public search and observed-link navigation are available.")
    print("Every navigation requires typing execute.")

    browser.start()

    try:
        while True:
            goal = input("\nYou: ").strip()

            if goal.lower() in {"q", "quit", "exit"}:
                break

            if not goal:
                continue

            action = agent.first_action(goal)
            actions_taken = 0

            while True:
                print()
                print(action.pretty())

                if action.kind in {"done", "clarify", "reject"}:
                    break

                if actions_taken >= max_actions:
                    print(
                        f"\nStopped after {max_actions} browser actions. "
                        "Ask a narrower follow-up request."
                    )
                    break

                decision = input(
                    "\nType execute to run this one browser action: "
                ).strip().lower()

                if decision != "execute":
                    print("Stopped. No browser action was executed.")
                    break

                state = execute_action(browser, action)
                actions_taken += 1

                print("\nObserved browser state:")
                print(state.pretty())

                action = agent.next_action(goal, state)

    except Exception as error:
        print(f"\nBrowser agent error: {error}")

    finally:
        browser.stop()
        print("Browser closed.")


if __name__ == "__main__":
    main()