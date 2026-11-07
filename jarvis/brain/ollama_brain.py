"""The chat brain: a small local language model running in Ollama."""
import time

import ollama

SYSTEM_PROMPT = (
    "You are {name}, a friendly voice assistant running on {user}'s own computer. "
    "Your replies are spoken out loud, so answer in 1 to 3 short, natural sentences. "
    "Use plain text only: no lists, no markdown, no emojis, no special symbols. "
    "If you do not know something, or it needs live information such as news, "
    "weather or prices, say so briefly instead of guessing. "
    "Never claim you can see, hear or do things you cannot do. "
    "You cannot see anything yourself. If the user asks what you can see, "
    "tell them to ask: what do you see?"
)


class OllamaBrain:
    def __init__(self, cfg):
        settings = cfg["brain"]["ollama"]
        self.model = settings["model"]
        self.keep_alive = settings["keep_alive"]
        self.options = {
            "num_ctx": settings["context"],
            "num_predict": settings["max_reply_tokens"],
            "temperature": 0.7,
            "top_p": 0.9,
        }
        if settings["threads"]:
            self.options["num_thread"] = settings["threads"]

        self.system = {
            "role": "system",
            "content": SYSTEM_PROMPT.format(
                name=cfg["assistant"]["name"], user=cfg["assistant"]["user_name"]
            ),
        }
        self.max_messages = cfg["brain"]["history_turns"] * 2
        self.history = []
        self.first_token_ms = None

    def warm_up(self):
        """Loads the model into memory now, so the first real question is fast."""
        ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": "hi"}],
            think=False,
            options={"num_predict": 1},
            keep_alive=self.keep_alive,
        )

    def stream(self, text):
        """Yields the reply token by token."""
        self.first_token_ms = None
        messages = [self.system] + self.history + [{"role": "user", "content": text}]
        reply = ""
        start = time.perf_counter()
        try:
            for part in ollama.chat(
                model=self.model,
                messages=messages,
                stream=True,
                think=False,
                options=self.options,
                keep_alive=self.keep_alive,
            ):
                token = part["message"]["content"]
                if not token:
                    continue
                if self.first_token_ms is None:
                    self.first_token_ms = (time.perf_counter() - start) * 1000
                reply += token
                yield token
        except Exception as error:
            print(f"\n  [brain error] {error}")
            reply = ""
            if "not found" in str(error).lower():
                yield "My language model is not installed yet."
            else:
                yield "Sorry, I can't reach my brain right now. Is Ollama running?"
        finally:
            if reply.strip():
                self.history += [
                    {"role": "user", "content": text},
                    {"role": "assistant", "content": reply},
                ]
                self.history = self.history[-self.max_messages:]



    def write_stream(self, prompt):
        """Yields text for a writing job (a poem, a paragraph...). No chat memory."""
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a writing assistant. Write exactly what the user asks for. "
                    "Output only the text itself: no title, no introduction, no explanation, "
                    "no markdown, no emojis."
                ),
            },
            {"role": "user", "content": prompt},
        ]
        options = dict(self.options)
        options["num_predict"] = 300  # longer than a chat reply
        for part in ollama.chat(
            model=self.model,
            messages=messages,
            stream=True,
            think=False,
            options=options,
            keep_alive=self.keep_alive,
        ):
            token = part["message"]["content"]
            if token:
                yield token