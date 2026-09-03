from faster_whisper import WhisperModel

from src.config import (
    WHISPER_MODEL,
    WHISPER_LANGUAGE,
    WHISPER_BEAM_SIZE,
    WHISPER_MIN_SILENCE_MS,
)


class WhisperService:

    def __init__(self):

        print("Loading Whisper model...")

        self.model = WhisperModel(
            WHISPER_MODEL,
            device="cpu",
            compute_type="int8",
        )

        print("✅ Whisper model loaded.\n")

    def transcribe(self, audio):

        # Convert (samples, 1) -> (samples,)
        audio = audio.flatten()

        segments, info = self.model.transcribe(
            audio,
            language=WHISPER_LANGUAGE,
            beam_size=WHISPER_BEAM_SIZE,
            vad_filter=True,
            vad_parameters={
                "min_silence_duration_ms": WHISPER_MIN_SILENCE_MS,
            },
        )

        text = " ".join(
            segment.text
            for segment in segments
        )

        return text.strip()