import numpy as np

from src.audio.microphone import Microphone
from src.speech.whisper_model import WhisperService


SAMPLE_RATE = 16000
BLOCK_SIZE = 512

WINDOW_SECONDS = 15
STEP_SECONDS = 5
TEST_SECONDS = 35

WINDOW_BLOCKS = int(WINDOW_SECONDS * SAMPLE_RATE / BLOCK_SIZE)
STEP_BLOCKS = int(STEP_SECONDS * SAMPLE_RATE / BLOCK_SIZE)


def transcribe_window(whisper, audio):
    segments, _ = whisper.model.transcribe(
        audio,
        language="en",
        beam_size=5,
        vad_filter=True,
        vad_parameters={
            "min_silence_duration_ms": 500,
        },
    )

    results = []

    for segment in segments:
        text = segment.text.strip()

        if text:
            results.append({
                "start": segment.start,
                "end": segment.end,
                "text": text,
            })

    return results


def main():
    microphone = Microphone()
    whisper = WhisperService()

    audio_blocks = []

    total_blocks = int(
        TEST_SECONDS * SAMPLE_RATE / BLOCK_SIZE
    )

    print("=" * 65)
    print("ROLLING WHISPER TIMESTAMP DIAGNOSTIC")
    print("=" * 65)
    print()
    print("The test runs for approximately 35 seconds.")
    print()
    print("Speak continuously and naturally.")
    print()
    print("Example:")
    print(
        "Today I am testing my personal assistant. "
        "It should continuously listen to conversations "
        "and remember important information. "
        "I am speaking naturally without stopping. "
        "The system should eventually detect important keywords "
        "and send the surrounding context to the AI."
    )
    print()
    input("Press ENTER when ready...")
    print()
    print("🎤 START SPEAKING NOW")
    print()

    microphone.start()

    try:
        for block_number in range(total_blocks):

            audio_blocks.append(microphone.read())

            if len(audio_blocks) < WINDOW_BLOCKS:
                continue

            if (
                (block_number + 1 - WINDOW_BLOCKS) % STEP_BLOCKS
                != 0
            ):
                continue

            window_start_block = (
                len(audio_blocks) - WINDOW_BLOCKS
            )

            window_start_time = (
                window_start_block
                * BLOCK_SIZE
                / SAMPLE_RATE
            )

            window_end_time = (
                len(audio_blocks)
                * BLOCK_SIZE
                / SAMPLE_RATE
            )

            audio = np.concatenate(
                audio_blocks[-WINDOW_BLOCKS:],
                axis=0,
            ).flatten()

            print()
            print("=" * 65)
            print(
                f"WINDOW AUDIO: "
                f"{window_start_time:.2f}s → "
                f"{window_end_time:.2f}s"
            )
            print("=" * 65)

            try:
                segments = transcribe_window(
                    whisper,
                    audio,
                )

                if not segments:
                    print("[no speech detected]")
                    continue

                for segment in segments:

                    # Convert window-relative timestamp
                    # to global microphone time.
                    global_start = (
                        window_start_time
                        + segment["start"]
                    )

                    global_end = (
                        window_start_time
                        + segment["end"]
                    )

                    print(
                        f"[{global_start:6.2f}s → "
                        f"{global_end:6.2f}s] "
                        f"{segment['text']!r}"
                    )

            except Exception as error:
                print(f"Whisper error: {error}")

    except KeyboardInterrupt:
        print("\nStopping test...")

    finally:
        microphone.stop()

    print()
    print("=" * 65)
    print("ROLLING TIMESTAMP TEST COMPLETED")
    print("=" * 65)
    print("No project source files were modified.")


if __name__ == "__main__":
    main()