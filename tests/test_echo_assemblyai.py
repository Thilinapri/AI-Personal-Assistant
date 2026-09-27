# tests/test_echo_assemblyai.py

import time

import numpy as np

from src.audio.microphone import Microphone
from src.speech.assemblyai_service import AssemblyAIService


# ============================================================
# Configuration
# ============================================================

RECORD_SECONDS = 10


# ============================================================
# Main test
# ============================================================

def main():

    print()
    print("=" * 60)
    print("EchoMind - Microphone → AssemblyAI Test")
    print("=" * 60)

    microphone = None

    try:

        # ----------------------------------------------------
        # 1. Initialize AssemblyAI
        # ----------------------------------------------------

        print()
        print("☁️ Initializing AssemblyAI service...")

        stt_service = AssemblyAIService()

        print(
            "✅ AssemblyAI service initialized."
        )

        # ----------------------------------------------------
        # 2. Initialize EchoMind microphone
        # ----------------------------------------------------

        print()
        print(
            "🎙️ Starting EchoMind microphone..."
        )

        microphone = Microphone()

        microphone.start()

        print(
            "✅ EchoMind microphone started."
        )

        # ----------------------------------------------------
        # 3. Record audio
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print(
            f"🎧 Recording for "
            f"{RECORD_SECONDS} seconds..."
        )
        print(
            "Speak normally into the laptop microphone."
        )
        print("=" * 60)

        audio_chunks = []

        start_recording = time.perf_counter()

        while (
            time.perf_counter()
            - start_recording
            < RECORD_SECONDS
        ):

            audio_block = microphone.read()

            if audio_block is None:
                continue

            # Microphone.read() returns a block
            # with shape (BLOCK_SIZE, 1).
            #
            # Convert it into a simple 1-D array.
            audio_block = np.asarray(
                audio_block
            ).flatten()

            audio_chunks.append(
                audio_block
            )

        print()
        print(
            "✅ Recording finished."
        )

        # ----------------------------------------------------
        # 4. Stop microphone
        # ----------------------------------------------------

        microphone.stop()

        microphone = None

        print(
            "🎤 EchoMind microphone stopped."
        )

        # ----------------------------------------------------
        # 5. Check whether audio was captured
        # ----------------------------------------------------

        if not audio_chunks:

            print()
            print(
                "❌ No audio blocks were received."
            )

            return

        # ----------------------------------------------------
        # 6. Combine all audio blocks
        # ----------------------------------------------------

        audio = np.concatenate(
            audio_chunks
        )

        print()
        print(
            f"📦 Audio blocks collected: "
            f"{len(audio_chunks)}"
        )

        print(
            f"📊 Total samples: "
            f"{len(audio)}"
        )

        # ----------------------------------------------------
        # 7. Calculate captured audio duration
        # ----------------------------------------------------

        audio_duration = (
            len(audio) / 16000
        )

        print(
            f"⏱️ Captured audio duration: "
            f"{audio_duration:.2f} seconds"
        )

        # ----------------------------------------------------
        # 8. Check microphone signal level
        # ----------------------------------------------------

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
            f"🔊 Peak level: "
            f"{peak:.6f}"
        )

        print(
            f"🔊 RMS level: "
            f"{rms:.6f}"
        )

        if peak < 0.001:

            print()
            print(
                "⚠️ WARNING:"
            )

            print(
                "The EchoMind microphone signal "
                "appears to be almost silent."
            )

        else:

            print()
            print(
                "✅ EchoMind microphone captured "
                "a valid audio signal."
            )

        # ----------------------------------------------------
        # 9. Send audio through AssemblyAIService
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print(
            "☁️ Sending EchoMind audio "
            "to AssemblyAI..."
        )
        print("=" * 60)

        start_stt = time.perf_counter()

        transcript = (
            stt_service.transcribe(
                audio
            )
        )

        stt_elapsed = (
            time.perf_counter()
            - start_stt
        )

        # ----------------------------------------------------
        # 10. Display result
        # ----------------------------------------------------

        print()
        print("=" * 60)
        print("RESULT")
        print("=" * 60)

        print()
        print(
            f"⏱️ Total AssemblyAIService time: "
            f"{stt_elapsed:.2f} seconds"
        )

        print()

        print(
            "📝 Transcript:"
        )

        if transcript:

            print(
                transcript
            )

        else:

            print(
                "[No speech detected]"
            )

        print()
        print("=" * 60)

        if transcript:

            print(
                "✅ ECHOMIND MICROPHONE → "
                "ASSEMBLYAI TEST PASSED"
            )

            print()
            print(
                "The EchoMind Microphone class "
                "successfully captured audio and "
                "AssemblyAI successfully "
                "transcribed it."
            )

        else:

            print(
                "⚠️ AssemblyAI responded, "
                "but no speech was detected."
            )

        print("=" * 60)
        print()

    except KeyboardInterrupt:

        print()
        print(
            "🛑 Test interrupted."
        )

    except Exception as error:

        print()
        print(
            "❌ Test failed:"
        )

        print(
            f"{type(error).__name__}: "
            f"{error}"
        )

    finally:

        if microphone is not None:

            try:
                microphone.stop()
            except Exception:
                pass

        print()
        print(
            "Test finished."
        )


if __name__ == "__main__":
    main()