import numpy as np

from src.audio.microphone import Microphone
from src.speech.whisper_model import WhisperService


SAMPLE_RATE = 16000
BLOCK_SIZE = 512

# Internal Whisper window.
WINDOW_SECONDS = 8
WINDOW_BLOCKS = int(WINDOW_SECONDS * SAMPLE_RATE / BLOCK_SIZE)

# How much new audio arrives before another transcription.
STEP_SECONDS = 3
STEP_BLOCKS = int(STEP_SECONDS * SAMPLE_RATE / BLOCK_SIZE)

TEST_SECONDS = 60


def main():
    microphone = Microphone()
    whisper = WhisperService()

    audio_blocks = []
    total_blocks = int(TEST_SECONDS * SAMPLE_RATE / BLOCK_SIZE)

    print("=" * 60)
    print("LIVE TRANSCRIPTION DIAGNOSTIC")
    print("=" * 60)
    print()
    print("The microphone will listen for 60 seconds.")
    print()
    print("Speak naturally during the test.")
    print("For example:")
    print(
        "Today I am testing my personal assistant. "
        "It should continuously transcribe my conversation "
        "without speech started and speech ended detection."
    )
    print()
    input("Press ENTER when you are ready...")
    print()
    print("🎤 START SPEAKING NOW")
    print()

    microphone.start()

    try:
        for block_number in range(total_blocks):

            audio_blocks.append(microphone.read())

            # Do not transcribe until enough audio exists.
            if len(audio_blocks) < WINDOW_BLOCKS:
                continue

            # Only transcribe every STEP_BLOCKS.
            if (
                (block_number + 1 - WINDOW_BLOCKS) % STEP_BLOCKS
                != 0
            ):
                continue

            window = np.concatenate(
                audio_blocks[-WINDOW_BLOCKS:],
                axis=0,
            ).flatten()

            print()
            print("-" * 60)
            print("TRANSCRIBING...")
            print("-" * 60)

            try:
                segments, info = whisper.model.transcribe(
                    window,
                    language="en",
                    beam_size=5,
                    vad_filter=True,
                    vad_parameters={
                        "min_silence_duration_ms": 500,
                    },
                )

                text = " ".join(
                    segment.text.strip()
                    for segment in segments
                    if segment.text.strip()
                )

                if text:
                    print(f"📝 {text}")
                else:
                    print("📝 [no speech detected]")

            except Exception as error:
                print(f"Whisper error: {error}")

    except KeyboardInterrupt:
        print("\nStopping test...")

    finally:
        microphone.stop()

    print()
    print("=" * 60)
    print("LIVE TRANSCRIPTION TEST COMPLETED")
    print("=" * 60)
    print("No project source files were modified.")


if __name__ == "__main__":
    main()