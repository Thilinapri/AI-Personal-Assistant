import numpy as np

from src.audio.microphone import Microphone
from src.speech.whisper_model import WhisperService


CAPTURE_SECONDS = 10


def calculate_rms(audio):
    return float(np.sqrt(np.mean(audio ** 2)))


def calculate_block_rms(audio, block_size=512):
    values = []

    for start in range(0, len(audio), block_size):
        block = audio[start:start + block_size]

        if len(block) == 0:
            continue

        values.append(calculate_rms(block))

    return values


def main():
    microphone = Microphone()

    try:
        print("=" * 60)
        print("Continuous Whisper diagnostic")
        print("=" * 60)

        microphone.start()

        print()
        print("NOW SPEAK")
        print("Speak continuously for about 5 seconds.")
        print()
        print("Example:")
        print(
            "This is a test of my artificial intelligence "
            "personal assistant. It should listen to conversations "
            "and remember important information."
        )
        print()
        print("Capturing 10 seconds...")

        blocks = []

        number_of_blocks = int(
            CAPTURE_SECONDS * 16000 / 512
        )

        for _ in range(number_of_blocks):
            audio = microphone.read()
            blocks.append(audio)

        audio = np.concatenate(blocks, axis=0)

        print()
        print("=== AUDIO MEASUREMENTS ===")

        duration = len(audio) / 16000

        block_rms = calculate_block_rms(audio)

        print(f"Shape: {audio.shape}")
        print(f"Duration: {duration:.3f} seconds")
        print(f"RMS: {calculate_rms(audio):.8f}")
        print(f"Peak: {np.max(np.abs(audio)):.8f}")
        print(f"Min: {np.min(audio):.8f}")
        print(f"Max: {np.max(audio):.8f}")
        print(f"Min block RMS: {min(block_rms):.8f}")
        print(f"Max block RMS: {max(block_rms):.8f}")
        print(f"Average block RMS: {np.mean(block_rms):.8f}")

        whisper = WhisperService()

        print()
        print("=" * 60)
        print("=== WHISPER WITHOUT VAD ===")
        print("=" * 60)

        try:
            # Use the existing WhisperService.
            result_without_vad = whisper.model.transcribe(
                audio.flatten(),
                language="en",
                beam_size=5,
                vad_filter=False,
            )

            segments_without_vad, _ = result_without_vad

            text_without_vad = " ".join(
                segment.text.strip()
                for segment in segments_without_vad
                if segment.text.strip()
            )

            print(f"Transcription: {text_without_vad!r}")

        except Exception as error:
            print(f"Whisper without VAD failed: {error}")

        print()
        print("=" * 60)
        print("=== WHISPER WITH SILERO VAD ===")
        print("=" * 60)

        try:
            result_with_vad = whisper.model.transcribe(
                audio.flatten(),
                language="en",
                beam_size=5,
                vad_filter=True,
                vad_parameters={
                    "min_silence_duration_ms": 500,
                },
            )

            segments_with_vad, _ = result_with_vad

            text_with_vad = " ".join(
                segment.text.strip()
                for segment in segments_with_vad
                if segment.text.strip()
            )

            print(f"Transcription: {text_with_vad!r}")

        except Exception as error:
            print(f"Whisper with VAD failed: {error}")

    finally:
        microphone.stop()

    print()
    print("Diagnostic completed.")
    print("No project files were modified.")


if __name__ == "__main__":
    main()