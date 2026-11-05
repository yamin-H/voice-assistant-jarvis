"""Picks the text-to-speech engine named in config.yaml."""


def load_tts(cfg):
    engine = cfg["tts"]["engine"]
    if engine == "paradee":
        from jarvis.tts.paradee_engine import ParadeeTTS
        return ParadeeTTS(cfg)
    if engine == "piper":
        from jarvis.tts.piper_engine import PiperTTS
        return PiperTTS(cfg)
    if engine == "kokoro":
        from jarvis.tts.kokoro_engine import KokoroTTS
        return KokoroTTS(cfg)
    raise ValueError(f"Unknown TTS engine: {engine}")