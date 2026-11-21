import threading
from datetime import datetime


class AudioWorker:
    """Processes completed audio segments from the audio queue."""

    def __init__(
    self,
    audio_queue,
    stt_service,
    transcript_buffer,
    keyword_filter,
    memory_engine,
    memory_manager,
    transcript_callback=None,
):
        self.audio_queue = audio_queue
        self.stt_service = stt_service
        self.transcript_buffer = transcript_buffer
        self.keyword_filter = keyword_filter
        self.memory_engine = memory_engine
        self.memory_manager = memory_manager
        self.transcript_callback = transcript_callback
        self._stop_event = threading.Event()

    def stop(self):
        """Prevent any further queued audio from being processed."""

        self._stop_event.set()

    def run(self):
        """Consume audio from the queue until a sentinel is received."""

        while True:
            audio = self.audio_queue.get()

            try:
                if audio is None:
                    print("Audio worker stopped.")
                    return

                if self._stop_event.is_set():
                    continue

                self.process_audio(audio)

            except Exception as error:
                print(
                    "[AUDIO] Worker chunk failed; continuing: "
                    f"{type(error).__name__}"
                )

            finally:
                self.audio_queue.task_done()
                if audio is not None:
                    print("[AUDIO] Waiting for next chunk.")

    def process_audio(self, audio):
        """Transcribe audio and process keyword-triggered memories."""

        # -------------------------------------------------
        # 1. Speech-to-text transcription
        # -------------------------------------------------

        try:
            print("[STT] Starting transcription.")
            transcription = self.stt_service.transcribe(audio)
            print("[STT] Transcription completed.")

            if self._stop_event.is_set():
                print(
                    "🛑 Audio processing cancelled during shutdown."
                )
                return

        except Exception as error:
            print(
                "[STT] Transcription failed: "
                f"{type(error).__name__}"
            )
            return

        transcription = transcription.strip()

        if not transcription:
            return

               # Send completed transcription to the display
        if self.transcript_callback is not None:
            try:
                self.transcript_callback(transcription)
            except Exception as error:
                print(
                    "[DISPLAY] Transcript update failed: "
                    f"{type(error).__name__}"
                )

        # -------------------------------------------------
        # 2. Add transcription to the session transcript buffer
        # -------------------------------------------------

        try:
            entry_id, context = (
                self.transcript_buffer.add_with_context(
                    transcription,
                    before=2,
                    after=0,
                )
            )

            print("[AUDIO] Transcript buffered for memory analysis.")

        except Exception as error:
            print(
                "[AUDIO] Transcript buffering failed: "
                f"{type(error).__name__}"
            )
            return

        # -------------------------------------------------
        # 3. Check immediate keywords
        # -------------------------------------------------

        try:
            should_process = (
                self.keyword_filter.should_process(
                    transcription
                )
            )

            if should_process:
                print("[KEYWORD] Immediate memory trigger detected.")

        except Exception as error:
            print(
                "[KEYWORD] Detection failed: "
                f"{type(error).__name__}"
            )
            return

        # Keep normal conversation in the session buffer.
        if not should_process:
            return

        # -------------------------------------------------
        # 4. Immediate Gemini processing
        # -------------------------------------------------

        try:
            print("[MEMORY] Extraction started.")

            if self._stop_event.is_set():
                print(
                    "🛑 Memory processing cancelled during shutdown."
                )
                return

            result = self.memory_engine.process(
                mode="immediate",
                sentences=context,
                current_time=datetime.now(),
            )

            memories = self._validate_extracted_memories(result)
            print(
                "[MEMORY] Extraction completed: "
                f"{len(memories)} candidate(s)."
            )
            print("[MEMORY] Validation completed.")

        except Exception as error:
            print(
                "[MEMORY] Extraction failed: "
                f"{type(error).__name__}"
            )
            return

        # Gemini found nothing.
        if not memories:
            print("[MEMORY] No useful memories found.")
            return

        # -------------------------------------------------
        # 5. Store memories using MemoryManager
        # -------------------------------------------------

        try:
            print(f"[DATABASE] Sending {len(memories)} memories to local storage.")
            stored_ids = self.memory_manager.store_memories(memories)
            stored_count = len(stored_ids or [])
            print(
                "[DATABASE] Local storage returned IDs for "
                f"{stored_count}/{len(memories)} memories."
            )

            if stored_count != len(memories):
                print(
                    "[DATABASE] Save incomplete; transcript retained "
                    "for later processing."
                )
                return

            print("[DATABASE] All extracted memories confirmed by local storage.")

        except Exception as error:
            print(
                "[DATABASE] Memory storage failed: "
                f"{type(error).__name__}"
            )
            return

        # -------------------------------------------------
        # 6. Remove immediately processed transcript
        # -------------------------------------------------

        try:
            self.transcript_buffer.remove(entry_id)

            print(
                "🗑️ Immediate transcript removed "
                "from session buffer."
            )

        except Exception as error:
            print(
                "[AUDIO] Transcript cleanup failed: "
                f"{type(error).__name__}"
            )

    @staticmethod
    def _validate_extracted_memories(result):
        """Check the existing local database fields before storage."""

        if not isinstance(result, dict):
            raise ValueError("Memory extraction result must be an object.")

        memories = result.get("memories")
        if not isinstance(memories, list):
            raise ValueError("Memory extraction result must contain a list.")

        required_fields = {
            "category",
            "title",
            "content",
            "date",
            "time",
            "notification",
        }
        for memory in memories:
            if not isinstance(memory, dict):
                raise ValueError("Each extracted memory must be an object.")
            if not required_fields.issubset(memory):
                raise ValueError("An extracted memory is missing database fields.")
            if any(
                not isinstance(memory[field], str)
                for field in ("category", "title", "content", "date", "time")
            ):
                raise ValueError("Extracted memory text fields are invalid.")
            if not isinstance(memory["notification"], bool):
                raise ValueError("Extracted memory notification field is invalid.")

        return memories
