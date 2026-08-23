import re
import numpy as np

from src.audio.microphone import Microphone
from src.speech.whisper_model import WhisperService


SAMPLE_RATE = 16000
BLOCK_SIZE = 512

WINDOW_SECONDS = 8
STEP_SECONDS = 3
TEST_SECONDS = 45

WINDOW_BLOCKS = int(WINDOW_SECONDS * SAMPLE_RATE / BLOCK_SIZE)
STEP_BLOCKS = int(STEP_SECONDS * SAMPLE_RATE / BLOCK_SIZE)


def normalize_words(text):
    return re.findall(r"\b[\w']+\b", text.lower())


def find_new_text(previous_text, current_text):
    """
    Find the portion of current_text that appears after
    the longest matching suffix of previous_text.
    """

    previous_words = normalize_words(previous_text)
    current_words = normalize_words(current_text)

    if not current_words:
        return ""

    max_overlap = min(len(previous_words), len(current_words))

    for overlap in range(max_overlap, 0, -1):
        if previous_words[-overlap:] == current_words[:overlap]:
            return " ".join(current_words[overlap:])

    # No reliable overlap found.
    # Return the current transcription so we don't silently lose speech.
    return current_text.strip()


def transcribe(whisper, audio):
    segments, _ = whisper.model.transcribe(
        audio,
        language="en",
        beam_size=5,
        vad_filter=True,
        vad_parameters={
            "min_silence_duration_ms": 500,
        },
    )

    return " ".join(
        segment.text.strip()
        for segment in segments
        if segment.text.strip()
    )


def main():
    microphone = Microphone()
    whisper = WhisperService()

    audio_blocks = []
    previous_text = ""

    total_blocks = int(TEST_SECONDS * SAMPLE_RATE / BLOCK_SIZE)

    print("=" * 60)
    print("TRANSCRIPT DEDUPLICATION DIAGNOSTIC")
    print("=" * 60)
    print()
    print("The test runs for approximately 45 seconds.")
    print("Speak continuously and naturally.")
    print()
    print("Example:")
    print(
        "Today I am testing my personal assistant. "
        "The assistant should continuously listen to conversations "
        "and remember important information. "
        "This test checks whether repeated Whisper overlap can be "
        "converted into one continuous transcript."
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

            window = np.concatenate(
                audio_blocks[-WINDOW_BLOCKS:],
                axis=0,
            ).flatten()

            print()
            print("-" * 60)
            print("WHISPER WINDOW")
            print("-" * 60)

            try:
                current_text = transcribe(whisper, window)

                new_text = find_new_text(
                    previous_text,
                    current_text,
                )

                print(f"FULL WHISPER : {current_text!r}")
                print(f"NEW TEXT     : {new_text!r}")

                if new_text:
                    print()
                    print(f"➡ NEW TRANSCRIPT: {new_text}")

                previous_text = current_text

            except Exception as error:
                print(f"Whisper error: {error}")

    except KeyboardInterrupt:
        print("\nStopping test...")

    finally:
        microphone.stop()

    print()
    print("=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)
    print()
    print("No project source files were modified.")


if __name__ == "__main__":
    main()