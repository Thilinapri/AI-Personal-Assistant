import queue
import threading

import numpy as np

from src.config import SAMPLE_RATE, BLOCK_SIZE


class AudioChunker:
    """
    Continuously captures microphone audio and places
    fixed-duration audio chunks onto the AudioWorker queue.

    Speech-to-text processing is handled separately by
    AudioWorker.
    """

    CHUNK_SECONDS = 20
    MAX_CAPTURE_RECOVERY_ATTEMPTS = 3
    MAX_DATABASE_ERRORS = 3
    RECOVERY_BASE_DELAY_SECONDS = 0.5

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
        if (
            self._thread is not None
            and self._thread.is_alive()
        ):
            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run,
            name="AudioChunker",
            daemon=True,
        )

        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def join(self, timeout=None):
        if self._thread is not None:
            self._thread.join(
                timeout=timeout
            )

    def _run(self):
        print(
            "\n🎧 Continuous listening started...\n"
        )

        try:
            audio_buffer = np.empty(
                self.chunk_samples,
                dtype=np.float32,
            )

            position = 0
            is_paused = False
            database_errors = 0
            capture_errors = 0

            while not self._stop_event.is_set():
                try:
                    listening_enabled = (
                        self.database.get_listening_enabled()
                    )
                    database_errors = 0
                except Exception as error:
                    database_errors += 1
                    print(
                        "[AUDIO] Listening-state read failed "
                        f"({database_errors}/"
                        f"{self.MAX_DATABASE_ERRORS}): "
                        f"{type(error).__name__}"
                    )
                    if database_errors >= self.MAX_DATABASE_ERRORS:
                        print(
                            "[AUDIO] Capture stopped after repeated "
                            "listening-state errors."
                        )
                        return
                    if self._wait_before_retry(database_errors):
                        return
                    continue

                if not listening_enabled:

                    if not is_paused:
                        position = 0

                        try:
                            self.microphone.stop()
                        except Exception as error:
                            print(
                                "[AUDIO] Microphone stop failed while "
                                f"pausing: {type(error).__name__}"
                            )

                        is_paused = True

                        print(
                            "⏸️ Listening paused. "
                            "Microphone capture stopped."
                        )

                    self._stop_event.wait(0.5)

                    continue

                if is_paused:
                    try:
                        self.microphone.start()
                    except Exception as error:
                        capture_errors += 1
                        if capture_errors > self.MAX_CAPTURE_RECOVERY_ATTEMPTS:
                            print(
                                "[AUDIO] Capture stopped after repeated "
                                "microphone failures."
                            )
                            return
                        position = 0
                        if not self._recover_microphone(error):
                            return

                    is_paused = False

                    print(
                        "▶️ Listening resumed. "
                        "Microphone capture started."
                    )

                try:
                    audio = self.microphone.read()
                    capture_errors = 0
                except Exception as error:
                    capture_errors += 1
                    if capture_errors > self.MAX_CAPTURE_RECOVERY_ATTEMPTS:
                        print(
                            "[AUDIO] Capture stopped after repeated "
                            "microphone failures."
                        )
                        try:
                            self.microphone.stop()
                        except Exception as stop_error:
                            print(
                                "[AUDIO] Final stream cleanup reported: "
                                f"{type(stop_error).__name__}"
                            )
                        return
                    position = 0
                    if not self._recover_microphone(error):
                        return
                    is_paused = False
                    continue

                try:
                    samples = audio.shape[0]

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
                except Exception as error:
                    position = 0
                    print(
                        "[AUDIO] Invalid microphone block discarded: "
                        f"{type(error).__name__}"
                    )
                    continue

                position += samples_to_copy

                if position < self.chunk_samples:
                    continue

                chunk = audio_buffer.copy()

                position = 0

                print(
                    f"[AUDIO] Chunk captured ({self.CHUNK_SECONDS}s)."
                )

                self._enqueue_chunk(chunk)
                print("[AUDIO] Waiting for next chunk.")

        except Exception as error:

            print(
                "[AUDIO] Capture loop stopped by an unexpected error: "
                f"{type(error).__name__}"
            )

        finally:

            print(
                "🎧 Continuous listening stopped."
            )

    def _wait_before_retry(self, attempt):
        delay = min(
            self.RECOVERY_BASE_DELAY_SECONDS * (2 ** (attempt - 1)),
            2.0,
        )
        return self._stop_event.wait(delay)

    def _recover_microphone(self, error):
        """Reopen a failed stream with bounded backoff and no parallel stream."""
        print(
            "[AUDIO] Microphone capture failed; restarting stream: "
            f"{type(error).__name__}"
        )

        try:
            self.microphone.stop()
        except Exception as stop_error:
            print(
                "[AUDIO] Stream cleanup reported: "
                f"{type(stop_error).__name__}"
            )

        for attempt in range(1, self.MAX_CAPTURE_RECOVERY_ATTEMPTS + 1):
            if self._wait_before_retry(attempt):
                return False

            try:
                self.microphone.start()
                print("[AUDIO] Microphone stream recovered.")
                return True
            except Exception as restart_error:
                print(
                    "[AUDIO] Microphone restart failed "
                    f"({attempt}/{self.MAX_CAPTURE_RECOVERY_ATTEMPTS}): "
                    f"{type(restart_error).__name__}"
                )
                try:
                    self.microphone.stop()
                except Exception as stop_error:
                    print(
                        "[AUDIO] Stream cleanup reported: "
                        f"{type(stop_error).__name__}"
                    )

        print(
            "[AUDIO] Capture stopped after exhausting microphone "
            "restart attempts."
        )
        return False

    def _copy_audio_samples(
        self,
        audio_buffer,
        position,
        audio,
        samples_to_copy,
    ):
        """
        Copy microphone samples into the current
        audio buffer.

        The microphone normally returns an array
        shaped like:

        (samples, channels)
        """

        if samples_to_copy <= 0:
            return

        audio_buffer[
            position:position + samples_to_copy
        ] = audio[
            :samples_to_copy,
            0
        ]

    def _enqueue_chunk(self, chunk):
        """
        Add a completed audio chunk to the
        AudioWorker queue.

        This operation is non-blocking so microphone
        capture does not freeze while the AudioWorker
        is processing another audio chunk.
        """

        try:

            self.audio_queue.put_nowait(
                chunk
            )

            print(
                "📤 Audio chunk added to "
                "processing queue."
            )

        except queue.Full:

            print(
                "⚠️ Audio processing queue is full. "
                "Dropping audio chunk."
            )
