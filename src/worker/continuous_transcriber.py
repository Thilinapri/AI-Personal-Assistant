import threading

import numpy as np

from src.config import SAMPLE_RATE, BLOCK_SIZE


class ContinuousTranscriber:
    """
    Continuously captures microphone audio and places fixed-duration
    audio chunks onto the AudioWorker queue.

    Whisper performs speech detection inside each chunk using Silero VAD.
    """

    CHUNK_SECONDS = 20

    def __init__(self, microphone, audio_queue, database):
        self.microphone = microphone
        self.audio_queue = audio_queue
        self.database = database

        self.blocks_per_chunk = int(
            self.CHUNK_SECONDS * SAMPLE_RATE / BLOCK_SIZE
        )

        self.chunk_samples = (
            self.blocks_per_chunk * BLOCK_SIZE
        )

        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        """Start continuous microphone capture."""

        if (
            self._thread is not None
            and self._thread.is_alive()
        ):
            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run,
            name="ContinuousTranscriber",
            daemon=True,
        )

        self._thread.start()

    def stop(self):
        """Request the capture loop to stop."""

        self._stop_event.set()

    def join(self, timeout=None):
        """Wait for the capture thread to finish."""

        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def _run(self):
        print(
            "\n🎧 Continuous listening started...\n"
        )

        audio_buffer = np.empty(
            self.chunk_samples,
            dtype=np.float32,
        )

        position = 0
        is_paused = False

        try:
            while not self._stop_event.is_set():

                listening_enabled = (
                    self.database.get_listening_enabled()
                )

                # ---------------------------------
                # Pause Listening
                # ---------------------------------

                if not listening_enabled:

                    if not is_paused:
                        # Discard any partially captured audio.
                        position = 0

                        self.microphone.stop()

                        is_paused = True

                        print(
                            "⏸️ Listening paused. "
                            "Microphone capture stopped."
                        )

                    self._stop_event.wait(0.5)
                    continue

                # ---------------------------------
                # Resume Listening
                # ---------------------------------

                if is_paused:

                    self.microphone.start()

                    is_paused = False

                    print(
                        "▶️ Listening resumed. "
                        "Microphone capture started."
                    )

                # ---------------------------------
                # Capture Audio
                # ---------------------------------

                audio = self.microphone.read()

                samples = audio.shape[0]

                audio_buffer[
                    position:position + samples
                ] = audio[:, 0]

                position += samples

                if position < self.chunk_samples:
                    continue

                chunk = audio_buffer.copy()
                position = 0

                print(
                    f"🎙️ Audio chunk ready "
                    f"({self.CHUNK_SECONDS}s)"
                )

                self.audio_queue.put(chunk)

        except Exception as error:
            print(
                "Continuous transcription "
                f"capture error: {error}"
            )

        finally:
            print(
                "🎧 Continuous listening stopped."
            )