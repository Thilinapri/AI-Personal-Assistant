import threading
from datetime import datetime


class AudioWorker:
    """Processes completed audio segments from the audio queue."""

    def __init__(
        self,
        audio_queue,
        whisper,
        transcript_buffer,
        keyword_filter,
        memory_engine,
        memory_manager,
    ):
        self.audio_queue = audio_queue
        self.whisper = whisper
        self.transcript_buffer = transcript_buffer
        self.keyword_filter = keyword_filter
        self.memory_engine = memory_engine
        self.memory_manager = memory_manager
        self._stop_event = threading.Event()

    def stop(self):
        """Prevent any further queued audio from being processed."""
        self._stop_event.set()

    def run(self):
        """Consume audio until the queue sentinel is received."""

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
                print(f"Audio worker error: {error}")

            finally:
                self.audio_queue.task_done()

    def process_audio(self, audio):
        """Transcribe audio and process keyword-triggered memories."""

        # -------------------------------------------------
        # 1. Whisper transcription
        # -------------------------------------------------

        try:
            transcription = self.whisper.transcribe(audio)

            print(
                f"\n📝 Whisper transcription: {transcription!r}"
            )

            if self._stop_event.is_set():
                print(
                    "🛑 Audio processing cancelled during shutdown."
                )
                return

        except Exception as error:
            print(
                f"Whisper transcription failed: {error}"
            )
            return

        if not transcription or not transcription.strip():
            return

        transcription = transcription.strip()

        # -------------------------------------------------
        # 2. Add transcription to conversation buffer
        # -------------------------------------------------

        try:
            entry_id, context = (
                self.transcript_buffer.add_with_context(
                    transcription,
                    before=2,
                    after=0,
                )
            )

            print(
                f"📥 Transcript buffered: {transcription}"
            )

        except Exception as error:
            print(
                f"Transcript buffering failed: {error}"
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

            print(
                f"🔎 Keyword detected: {should_process}"
            )

        except Exception as error:
            print(
                f"Keyword detection failed: {error}"
            )
            return

        # No immediate keyword.
        # Keep the transcript in the 20-minute buffer.
        if not should_process:
            return

        # -------------------------------------------------
        # 4. Immediate Gemini processing
        # -------------------------------------------------

        try:
            print("📋 Immediate context:")
            print(context)

            print(
                "🤖 Sending immediate context to Gemini..."
            )

            if self._stop_event.is_set():
                print(
                    "🛑 Memory processing cancelled during shutdown."
                )
                return

            result = self.memory_engine.process(
                mode="immediate",
                text=context,
                current_time=datetime.now(),
            )

            print(
                f"🤖 Gemini result: {result!r}"
            )

            memories = result["memories"]

            print(
                f"🧠 Memories extracted: {memories!r}"
            )

        except Exception as error:
            print(
                f"Immediate memory processing failed: {error}"
            )
            return

        # Gemini found nothing.
        if not memories:
            print("ℹ️ Gemini found no memories.")
            return

        # -------------------------------------------------
        # 5. Store memories using the new MemoryManager
        # -------------------------------------------------

        try:
            self.memory_manager.store_memories(
                memories
            )

            print(
                "💾 Memories saved through MemoryManager."
            )

        except Exception as error:
            print(
                f"Saving memories failed: {error}"
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
                f"Removing immediate transcript failed: {error}"
            )