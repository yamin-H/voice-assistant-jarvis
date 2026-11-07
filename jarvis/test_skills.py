"""Tests skills by typing what you would say. No microphone needed.

Run:  python -m jarvis.test_skills          (without the writing brain)
      python -m jarvis.test_skills brain    (with the writing brain, for "write a poem")
Actions wait 3 seconds first, so you can click on a window if you want to.
Press Enter on an empty line to see if a timer or reminder has gone off.
"""
import sys
import time

from jarvis.config import load_config
from jarvis.router import Router
from jarvis.scheduler import SCHEDULER, spoken


def main():
    cfg = load_config()
    brain = None
    if "brain" in sys.argv[1:]:
        from jarvis.brain import load_brain
        print("Loading the brain...")
        brain = load_brain(cfg)
        brain.warm_up()

    router = Router(cfg, vision=None, brain=brain)
    print("Type what you would say. Type q to quit.")
    print("(Say 'yes' or 'no' when it asks a question. Empty line = check timers.)")
    while True:
        text = input("\nYou: ").strip()
        if text.lower() in ("q", "quit"):
            break
        if not text:
            due = SCHEDULER.pop_due()
            if not due:
                print("  (nothing has gone off yet)")
            for item in due:
                print(f"  [{item['kind']} went off] JARVIS: {spoken(item)}")
            continue
        reply = router.route(text)
        if reply is None:
            print("  (no skill matched, so the chat brain would answer this)")
            continue
        skill = f" [skill: {router.last_match}]" if router.last_match else ""
        print(f"  JARVIS: {reply.text}{skill}")
        if reply.action:
            for n in (3, 2, 1):
                print(f"  acting in {n}...", end="\r", flush=True)
                time.sleep(1)
            message = reply.action()
            print("  done.            ")
            if isinstance(message, str) and message:
                print(f"  JARVIS: {message}")


if __name__ == "__main__":
    main()