"""Picks the chat brain named in config.yaml."""


def load_brain(cfg):
    engine = cfg["brain"]["engine"]

    if engine == "ollama":
        from jarvis.brain.ollama_brain import OllamaBrain
        return OllamaBrain(cfg)

    if engine == "groq":
        from jarvis.brain.groq_brain import GroqBrain
        return GroqBrain(cfg)

    raise ValueError(
        f"Unknown brain engine: {engine}. Expected 'ollama' or 'groq'."
    )