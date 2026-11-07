"""Test the isolated Jarvis Browser.

Run:
    python -m jarvis.test_browser

Commands:
    open example.com
    search official Python documentation
    observe
    q
"""

from jarvis.browser import BrowserSession
from jarvis.config import load_config


def main():
    cfg = load_config()
    browser = BrowserSession(cfg)

    print("Starting isolated Jarvis Browser...")
    browser.start()

    print("Commands:")
    print("  open <public URL>")
    print("  search <query>")
    print("  observe")
    print("  q")

    try:
        while True:
            command = input("\nBrowser: ").strip()

            if command.lower() in {"q", "quit", "exit"}:
                break

            if command == "observe":
                print()
                print(browser.observe().pretty())
                continue

            if command.startswith("open "):
                state = browser.open_url(command[5:])
                print()
                print(state.pretty())
                continue

            if command.startswith("search "):
                state = browser.search(command[7:])
                print()
                print(state.pretty())
                continue

            print("Unknown command. Use open, search, observe, or q.")

    except Exception as error:
        print(f"\nBrowser error: {error}")

    finally:
        browser.stop()
        print("Browser closed.")


if __name__ == "__main__":
    main()