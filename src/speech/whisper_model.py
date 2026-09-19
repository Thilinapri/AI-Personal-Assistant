import time

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

        start_time = time.perf_counter()

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
        ).strip()

        elapsed = time.perf_counter() - start_time

        audio_duration = len(audio) / 16000

        if audio_duration > 0:
            realtime_factor = elapsed / audio_duration
        else:
            realtime_factor = 0.0

        print(
            f"⏱️ Whisper: {elapsed:.2f}s "
            f"for {audio_duration:.2f}s audio "
            f"(RTF: {realtime_factor:.2f})"
        )

        return text