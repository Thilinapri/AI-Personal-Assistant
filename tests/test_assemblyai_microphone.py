# tests/test_assemblyai_microphone.py

import io
import os
import time
import wave

import numpy as np
import requests
import sounddevice as sd
from dotenv import load_dotenv


# ============================================================
# Configuration
# ============================================================

SAMPLE_RATE = 16000
CHANNELS = 1
RECORD_SECONDS = 10

# Laptop built-in microphone
MICROPHONE_DEVICE = 3

ASSEMBLYAI_ENDPOINT = (
    "https://sync.assemblyai.com/transcribe"
)

ASSEMBLYAI_MODEL = "universal-3-5-pro"


# ============================================================
# Load environment variables
# ============================================================

load_dotenv()

API_KEY = os.getenv("ASSEMBLYAI_API_KEY")


# ============================================================
# Validate API key
# ============================================================

if not API_KEY:
    raise RuntimeError(
        "ASSEMBLYAI_API_KEY was not found in .env"
    )


# ============================================================
# Convert NumPy audio to WAV
# ============================================================

def audio_to_wav(audio):
    """
    Convert NumPy float32 audio into
    mono 16-bit PCM WAV bytes.
    """

    audio = np.asarray(audio).flatten()

    audio = np.clip(
        audio,
        -1.0,
        1.0,
    )

    pcm_audio = (
        audio * 32767.0
    ).astype(np.int16)

    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as wav_file:

        wav_file.setnchannels(CHANNELS)

        wav_file.setsampwidth(2)

        wav_file.setframerate(SAMPLE_RATE)

        wav_file.writeframes(
            pcm_audio.tobytes()
        )

    buffer.seek(0)

    return buffer.read()


# ============================================================
# Record microphone
# ============================================================

def record_audio():

    print()
    print("=" * 50)
    print("Microphone Test")
    print("=" * 50)

    print()

    print(
        f"🎤 Microphone device: "
        f"{MICROPHONE_DEVICE}"
    )

    print(
        f"🎤 Recording for "
        f"{RECORD_SECONDS} seconds..."
    )

    print(
        "Speak normally during the recording."
    )

    print()

    audio = sd.rec(
        int(
            RECORD_SECONDS
            * SAMPLE_RATE
        ),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
        device=MICROPHONE_DEVICE,
    )

    sd.wait()

    print()
    print("✅ Recording finished.")

    # Show the recorded signal level.
    peak = float(
        np.max(
            np.abs(audio)
        )
    )

    rms = float(
        np.sqrt(
            np.mean(
                audio ** 2
            )
        )
    )

    print()
    print(
        f"🔊 Microphone peak level: "
        f"{peak:.6f}"
    )

    print(
        f"🔊 Microphone RMS level: "
        f"{rms:.6f}"
    )

    if peak < 0.001:

        print()
        print(
            "⚠️ WARNING: The microphone signal "
            "appears to be almost silent."
        )

    else:

        print()
        print(
            "✅ Microphone is producing audio."
        )

    return audio


# ============================================================
# Send audio to AssemblyAI
# ============================================================

def transcribe_with_assemblyai(audio):

    print()
    print("=" * 50)
    print("Sending audio to AssemblyAI")
    print("=" * 50)

    wav_bytes = audio_to_wav(audio)

    start_time = time.perf_counter()

    try:

        response = requests.post(
            ASSEMBLYAI_ENDPOINT,

            headers={
                "Authorization": API_KEY,
                "X-AAI-Model": ASSEMBLYAI_MODEL,
            },

            files={
                "audio": (
                    "microphone.wav",
                    wav_bytes,
                    "audio/wav",
                )
            },

            timeout=60,
        )

        elapsed = (
            time.perf_counter()
            - start_time
        )

        print()
        print(
            f"⏱️ Request completed in "
            f"{elapsed:.2f} seconds."
        )

        print(
            f"📡 HTTP status: "
            f"{response.status_code}"
        )

        response.raise_for_status()

    except requests.RequestException as error:

        print()
        print(
            "❌ AssemblyAI request failed."
        )

        print(
            f"Error: {error}"
        )

        if "response" in locals():

            print()
            print(
                "AssemblyAI response:"
            )

            print(
                response.text
            )

        raise

    result = response.json()

    transcript = (
        result.get("text", "")
        or ""
    ).strip()

    server_time_ms = (
        result.get(
            "request_time_ms"
        )
    )

    audio_duration_ms = (
        result.get(
            "audio_duration_ms"
        )
    )

    print()
    print("=" * 50)
    print("AssemblyAI Result")
    print("=" * 50)

    print()

    print(
        "📝 Transcript:"
    )

    print(
        transcript
        if transcript
        else "[No speech detected]"
    )

    print()

    if audio_duration_ms is not None:

        print(
            f"🎧 Audio duration: "
            f"{audio_duration_ms / 1000:.2f} seconds"
        )

    if server_time_ms is not None:

        print(
            f"⚙️ Server processing: "
            f"{server_time_ms:.0f} ms"
        )

    print()

    return transcript


# ============================================================
# Main
# ============================================================

def main():

    print()
    print("=" * 50)
    print("EchoMind - AssemblyAI Microphone Test")
    print("=" * 50)

    print()

    print(
        "🎙️ Selected laptop microphone:"
    )

    try:

        microphone_info = (
            sd.query_devices(
                MICROPHONE_DEVICE
            )
        )

        print(
            f"   {microphone_info['name']}"
        )

    except Exception as error:

        print(
            f"Could not read microphone "
            f"information: {error}"
        )

    print()

    print(
        "✅ AssemblyAI API key found."
    )

    try:

        audio = record_audio()

        transcript = (
            transcribe_with_assemblyai(
                audio
            )
        )

    except KeyboardInterrupt:

        print()
        print(
            "🛑 Test cancelled."
        )

        return

    except Exception as error:

        print()
        print(
            "❌ Test failed:"
        )

        print(error)

        return

    print()
    print("=" * 50)

    if transcript:

        print(
            "✅ ASSEMBLYAI TEST PASSED"
        )

        print()
        print(
            "Laptop microphone → "
            "AssemblyAI → transcript "
            "is working."
        )

    else:

        print(
            "⚠️ ASSEMBLYAI CONNECTED"
        )

        print()
        print(
            "AssemblyAI responded successfully, "
            "but no speech was detected."
        )

    print("=" * 50)
    print()


if __name__ == "__main__":
    main()