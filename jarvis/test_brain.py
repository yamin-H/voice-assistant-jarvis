"""Tests the chat brain without voice.

Run:  python -m jarvis.test_brain
      python -m jarvis.test_brain qwen3.5:2b-q4_K_M
"""
import sys
import time

from jarvis.brain import load_brain
from jarvis.brain.chunker import speakable_pieces
from jarvis.config import load_config


def main():
    cfg = load_config()
    if len(sys.argv) > 1:
        cfg["brain"]["ollama"]["model"] = sys.argv[1]
    print(f"Model: {cfg['brain']['ollama']['model']}")
    brain = load_brain(cfg)

    print("Loading model into memory...")
    start = time.perf_counter()
    try:
        brain.warm_up()
    except Exception as error:
        print(f"Could not use Ollama: {error}")
        print("Is Ollama running (tray icon)? Did you run the 'ollama pull' command?")
        return
    print(f"  loaded in {time.perf_counter() - start:.1f} s")

    print("\nType a question and press Enter. Type q to quit.")
    while True:
        text = input("\nYou: ").strip()
        if text.lower() in ("q", "quit", ""):
            break

        tokens = 0

        def counted():
            nonlocal tokens
            for token in brain.stream(text):
                tokens += 1
                yield token

        start = time.perf_counter()
        print("Jarvis: ", end="", flush=True)
        for piece in speakable_pieces(counted()):
            at = (time.perf_counter() - start) * 1000
            print(f"[{at:.0f} ms] {piece}  ", end="", flush=True)
        total = time.perf_counter() - start
        first = brain.first_token_ms or 0
        print(f"\n  first word: {first:.0f} ms | about {tokens / total:.1f} tokens/s | total {total:.1f} s")


if __name__ == "__main__":
    main()