from faster_whisper import WhisperModel

from src.config import WHISPER_MODEL


class WhisperService:

    def __init__(self):

        print("Loading Whisper model...")

        self.model = WhisperModel(
            WHISPER_MODEL,
            device="cpu",
            compute_type="int8"
        )

        print("✅ Whisper model loaded.\n")

    def transcribe(self, audio):

        # Convert (samples,1) -> (samples,)
        audio = audio.flatten()

        segments, info = self.model.transcribe(
    audio,
    language="en",
    beam_size=5,
    vad_filter=True,
    vad_parameters={
        "min_silence_duration_ms": 500,
    },
)

        text = ""

        for segment in segments:
            text += segment.text

        return text.strip()