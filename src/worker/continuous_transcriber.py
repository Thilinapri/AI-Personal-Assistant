import queue
import threading

import numpy as np

from src.config import SAMPLE_RATE, BLOCK_SIZE


class ContinuousTranscriber:
    """
    Continuously captures microphone audio and places fixed-duration
    audio chunks onto the AudioWorker queue.

    Whisper performs speech detection inside each chunk using Silero VAD.
    The queue insertion is non-blocking so microphone capture will not
    freeze when the AudioWorker is busy.
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

                # Protect against unexpected audio block sizes.
                remaining_samples = (
                    self.chunk_samples - position
                )

                samples_to_copy = min(
                    samples,
                    remaining_samples,
                )

                self._copy_audio_samples(
                    audio_buffer=audio_buffer,
                    position=position,
                    audio=audio,
                    samples_to_copy=samples_to_copy,
                )

                position += samples_to_copy

                if position < self.chunk_samples:
                    continue

                chunk = audio_buffer.copy()

                position = 0

                print(
                    "🎙️ Audio chunk ready "
                    f"({self.CHUNK_SECONDS}s)"
                )

                self._enqueue_chunk(chunk)

        except Exception as error:

            print(
                "Continuous transcription "
                f"capture error: {error}"
            )

        finally:

            print(
                "🎧 Continuous listening stopped."
            )

    def _copy_audio_samples(
        self,
        audio_buffer,
        position,
        audio,
        samples_to_copy,
    ):
        """
        Copy microphone samples into the current audio buffer.

        The microphone normally returns an array shaped like:
        (samples, channels)
        """

        if samples_to_copy <= 0:
            return

        audio_buffer[
            position:position + samples_to_copy
        ] = audio[:samples_to_copy, 0]

    def _enqueue_chunk(self, chunk):
        """
        Add a completed audio chunk to the AudioWorker queue.

        This operation is non-blocking so microphone capture does not
        freeze while Whisper is processing another audio chunk.
        """

        try:

            self.audio_queue.put_nowait(chunk)

            print(
                "📤 Audio chunk added to processing queue."
            )

        except queue.Full:

            print(
                "⚠️ Audio processing queue is full. "
                "Dropping audio chunk."
            )