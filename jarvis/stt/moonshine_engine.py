"""Moonshine speech-to-text. Audio goes in, text comes out."""
from moonshine_voice import (
    Transcriber,
    TranscriptEventListener,
    get_model_for_language,
)


class _Listener(TranscriptEventListener):
    def __init__(self, on_partial, on_final):
        super().__init__()
        self.on_partial = on_partial
        self.on_final = on_final

    def on_line_started(self, event):
        pass

    def on_line_text_changed(self, event):
        if self.on_partial:
            self.on_partial(event.line.text)

    def on_line_completed(self, event):
        if self.on_final:
            self.on_final(event.line.text)


class MoonshineSTT:
    def __init__(self, cfg):
        settings = cfg["stt"]["moonshine"]
        self.sample_rate = cfg["audio"]["sample_rate"]
        self.update_interval = settings["update_interval"]

        model_path, model_arch = get_model_for_language(settings["language"])
        print(f"Moonshine model: {model_arch}")
        self.transcriber = Transcriber(model_path=model_path, model_arch=model_arch)
        self.stream = None

    def start(self, on_partial=None, on_final=None):
        """on_partial(text) = live text while you talk. on_final(text) = sentence finished."""
        self.stream = self.transcriber.create_stream(update_interval=self.update_interval)
        self.stream.add_listener(_Listener(on_partial, on_final))
        self.stream.start()

    def feed(self, audio):
        """audio = numpy float32 array of microphone samples."""
        self.stream.add_audio(audio.tolist(), self.sample_rate)

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None