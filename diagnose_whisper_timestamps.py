import numpy as np

from src.audio.microphone import Microphone
from src.speech.whisper_model import WhisperService


SAMPLE_RATE = 16000
BLOCK_SIZE = 512

CAPTURE_SECONDS = 20


def main():
    microphone = Microphone()
    whisper = WhisperService()

    try:
        print("=" * 60)
        print("WHISPER TIMESTAMP DIAGNOSTIC")
        print("=" * 60)
        print()
        print("Speak naturally for about 15 seconds.")
        print()
        print("Example:")
        print(
            "Today I am testing my personal assistant. "
            "It should continuously listen to conversations "
            "and remember important information. "
            "I am speaking naturally without stopping."
        )
        print()

        input("Press ENTER when ready...")
        print()
        print("🎤 START SPEAKING NOW")
        print()

        microphone.start()

        blocks = []
        number_of_blocks = int(
            CAPTURE_SECONDS * SAMPLE_RATE / BLOCK_SIZE
        )

        for _ in range(number_of_blocks):
            blocks.append(microphone.read())

        audio = np.concatenate(blocks, axis=0).flatten()

        print()
        print("Audio captured.")
        print(f"Duration: {len(audio) / SAMPLE_RATE:.3f} seconds")
        print()

        print("=" * 60)
        print("WHISPER SEGMENTS WITHOUT VAD")
        print("=" * 60)

        segments, info = whisper.model.transcribe(
            audio,
            language="en",
            beam_size=5,
            vad_filter=False,
        )

        for number, segment in enumerate(segments, start=1):
            print(
                f"[{segment.start:7.2f}s → {segment.end:7.2f}s] "
                f"{segment.text.strip()!r}"
            )

        print()
        print("=" * 60)
        print("WHISPER SEGMENTS WITH SILERO VAD")
        print("=" * 60)

        segments, info = whisper.model.transcribe(
            audio,
            language="en",
            beam_size=5,
            vad_filter=True,
            vad_parameters={
                "min_silence_duration_ms": 500,
            },
        )

        for number, segment in enumerate(segments, start=1):
            print(
                f"[{segment.start:7.2f}s → {segment.end:7.2f}s] "
                f"{segment.text.strip()!r}"
            )

    except KeyboardInterrupt:
        print("\nStopping test...")

    finally:
        microphone.stop()

    print()
    print("=" * 60)
    print("DIAGNOSTIC COMPLETED")
    print("=" * 60)
    print("No project source files were modified.")


if __name__ == "__main__":
    main()