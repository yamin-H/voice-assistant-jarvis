"""Cloud chat brain powered by Groq.

This module only produces conversation text. It does not have permission to
control the computer. Tool planning will be added in a later phase.
"""

import os
import time

from groq import Groq


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


class GroqBrain:
    """Streaming conversational brain with the same interface as OllamaBrain."""

    def __init__(self, cfg):
        settings = cfg["brain"]["groq"]
        api_key = os.environ.get("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Set it as a Windows environment variable "
                "before using the Groq brain."
            )

        self.client = Groq(api_key=api_key)
        self.model = settings["model"]
        self.max_reply_tokens = settings["max_reply_tokens"]
        self.temperature = settings["temperature"]
        self.keep_alive = None  # Kept for interface compatibility with OllamaBrain.

        self.system = {
            "role": "system",
            "content": SYSTEM_PROMPT.format(
                name=cfg["assistant"]["name"],
                user=cfg["assistant"]["user_name"],
            ),
        }
        self.max_messages = cfg["brain"]["history_turns"] * 2
        self.history = []
        self.first_token_ms = None

    def warm_up(self):
        """Validate credentials and model availability before normal use."""
        self.client.chat.completions.create(
            model=self.model,
            messages=[
                self.system,
                {"role": "user", "content": "Reply with: ready"},
            ],
            max_completion_tokens=4,
            temperature=0,
        )

    def stream(self, text):
        """Yield the reply token by token and retain short conversation history."""
        self.first_token_ms = None
        messages = [self.system] + self.history + [
            {"role": "user", "content": text}
        ]
        reply = ""
        start = time.perf_counter()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                max_completion_tokens=self.max_reply_tokens,
                temperature=self.temperature,
            )

            for part in response:
                token = part.choices[0].delta.content or ""
                if not token:
                    continue

                if self.first_token_ms is None:
                    self.first_token_ms = (time.perf_counter() - start) * 1000

                reply += token
                yield token

        except Exception as error:
            print(f"\n  [Groq brain error] {error}")
            yield "Sorry, I cannot reach my cloud brain right now."

        finally:
            if reply.strip():
                self.history += [
                    {"role": "user", "content": text},
                    {"role": "assistant", "content": reply},
                ]
                self.history = self.history[-self.max_messages:]

    def write_stream(self, prompt):
        """Yield longer generated text without adding it to conversation memory."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a writing assistant. Write exactly what the user asks for. "
                        "Output only the text itself: no title, no introduction, no explanation, "
                        "no markdown, no emojis."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            stream=True,
            max_completion_tokens=300,
            temperature=self.temperature,
        )

        for part in response:
            token = part.choices[0].delta.content or ""
            if token:
                yield token