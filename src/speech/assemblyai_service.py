# src/speech/assemblyai_service.py

import io
import os
import time
import wave
from pathlib import Path

import numpy as np
import requests
from dotenv import load_dotenv

from src.config import SAMPLE_RATE, CHANNELS, STT_MODEL


# ============================================================
# Load .env from the EchoMind project root
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(
    dotenv_path=ENV_FILE
)


class AssemblyAIService:
    """
    Speech-to-text service using AssemblyAI's Sync API.

    Converts microphone float32 NumPy audio into
    16-bit PCM WAV audio and sends it to AssemblyAI.
    """

    ENDPOINT = "https://sync.assemblyai.com/transcribe"

    def __init__(self):
        self.api_key = os.getenv(
            "ASSEMBLYAI_API_KEY"
        )

        if not self.api_key:
            raise ValueError(
                "ASSEMBLYAI_API_KEY not found in environment."
            )

        self.model = STT_MODEL

        print(
            "🎤 AssemblyAI speech-to-text initialized."
        )

    def transcribe(self, audio):
        """
        Transcribe one audio chunk.

        Parameters
        ----------
        audio : numpy.ndarray
            Float32 microphone samples.

        Returns
        -------
        str
            Transcribed text.
        """

        if audio is None:
            raise ValueError(
                "Audio cannot be None."
            )

        # Convert input to a flat NumPy array.
        audio = np.asarray(
            audio
        ).flatten()

        # Nothing to transcribe.
        if audio.size == 0:
            return ""

        # Convert microphone audio to WAV bytes.
        wav_bytes = self._audio_to_wav(
            audio
        )

        audio_duration = (
            len(audio) / SAMPLE_RATE
        )

        start_time = time.perf_counter()

        try:

            response = requests.post(
                self.ENDPOINT,
                headers={
                    "Authorization": self.api_key,
                    "X-AAI-Model": self.model,
                },
                files={
                    "audio": (
                        "audio.wav",
                        wav_bytes,
                        "audio/wav",
                    )
                },
                timeout=60,
            )

            response.raise_for_status()

        except requests.RequestException as error:

            elapsed = (
                time.perf_counter()
                - start_time
            )

            print(
                f"❌ AssemblyAI request failed "
                f"after {elapsed:.2f}s: {error}"
            )

            raise

        elapsed = (
            time.perf_counter()
            - start_time
        )

        result = response.json()

        # Extract transcript.
        text = result.get(
            "text",
            ""
        ).strip()

        # AssemblyAI server processing time.
        server_time_ms = result.get(
            "request_time_ms"
        )

        print(
            f"⏱️ AssemblyAI request: "
            f"{elapsed:.2f}s for "
            f"{audio_duration:.2f}s audio"
        )

        if server_time_ms is not None:

            print(
                f"   Server processing: "
                f"{server_time_ms:.0f} ms"
            )

        print(
            f"📝 Transcript: {text!r}"
        )

        return text

    @staticmethod
    def _audio_to_wav(audio):
        """
        Convert float32 microphone samples into
        mono 16-bit PCM WAV bytes.
        """

        # Keep samples within valid audio range.
        audio = np.clip(
            audio,
            -1.0,
            1.0
        )

        # Convert float32 samples to signed 16-bit PCM.
        pcm_audio = (
            audio * 32767.0
        ).astype(
            np.int16
        )

        # Create an in-memory WAV file.
        buffer = io.BytesIO()

        with wave.open(
            buffer,
            "wb"
        ) as wav_file:

            wav_file.setnchannels(
                CHANNELS
            )

            wav_file.setsampwidth(
                2
            )

            wav_file.setframerate(
                SAMPLE_RATE
            )

            wav_file.writeframes(
                pcm_audio.tobytes()
            )

        buffer.seek(0)

        return buffer.read()