"""Picks the speech-to-text engine named in config.yaml."""


def load_stt(cfg):
    engine = cfg["stt"]["engine"]
    if engine == "moonshine":
        from jarvis.stt.moonshine_engine import MoonshineSTT
        return MoonshineSTT(cfg)
    raise ValueError(f"Unknown speech-to-text engine: {engine}")