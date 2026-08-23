import numpy as np

from src.audio.microphone import Microphone
from src.speech.whisper_model import WhisperService


SAMPLE_RATE = 16000
BLOCK_SIZE = 512

CHUNK_SECONDS = 5
CHUNK_BLOCKS = int(CHUNK_SECONDS * SAMPLE_RATE / BLOCK_SIZE)

NUMBER_OF_CHUNKS = 4


def rms(audio):
    return float(np.sqrt(np.mean(audio ** 2)))


def main():
    microphone = Microphone()
    whisper = None

    try:
        print("=" * 60)
        print("CHUNKED CONTINUOUS WHISPER TEST")
        print("=" * 60)

        microphone.start()

        print()
        print("The microphone is now listening continuously.")
        print()
        print("Speak naturally during the test.")
        print("For example:")
        print(
            "This is the first sentence of my personal assistant test. "
            "Now I am saying another sentence to check continuous "
            "transcription across multiple audio chunks."
        )
        print()
        print("The test will capture 4 chunks of 5 seconds each.")
        print("START SPEAKING NOW")
        print()

        whisper = WhisperService()

        for chunk_number in range(1, NUMBER_OF_CHUNKS + 1):

            blocks = []

            for _ in range(CHUNK_BLOCKS):
                blocks.append(microphone.read())

            audio = np.concatenate(blocks, axis=0).flatten()

            print()
            print("=" * 60)
            print(f"CHUNK {chunk_number}/{NUMBER_OF_CHUNKS}")
            print("=" * 60)

            print(f"Samples: {len(audio)}")
            print(f"Duration: {len(audio) / SAMPLE_RATE:.3f}s")
            print(f"RMS: {rms(audio):.8f}")
            print(f"Peak: {np.max(np.abs(audio)):.8f}")

            try:
                segments, info = whisper.model.transcribe(
                    audio,
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

                print()
                print(f"TRANSCRIPTION {chunk_number}:")
                print(repr(text))

            except Exception as error:
                print()
                print(f"Whisper error in chunk {chunk_number}: {error}")

        print()
        print("=" * 60)
        print("TEST COMPLETED")
        print("=" * 60)

    finally:
        microphone.stop()


if __name__ == "__main__":
    main()