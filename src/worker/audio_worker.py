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

    def run(self):
        """Consume audio until the queue sentinel is received."""

        while True:
            audio = self.audio_queue.get()

            try:
                if audio is None:
                    print("Audio worker stopped.")
                    return

                self.process_audio(audio)

            except Exception as error:
                # Keep the worker alive if an unexpected item-level failure occurs.
                print(f"Audio worker error: {error}")

            finally:
                self.audio_queue.task_done()

    def process_audio(self, audio):
        """Transcribe one audio segment and process keyword-triggered memories."""

        try:
            transcription = self.whisper.transcribe(audio)
            print(f"\n📝 Whisper transcription: {transcription!r}")

        except Exception as error:
            print(f"Whisper transcription failed: {error}")
            return

        if not transcription or not transcription.strip():
            return

        transcription = transcription.strip()

        try:
            # Every non-empty transcription stays in the local conversation buffer.
            entry_id, context = self.transcript_buffer.add_with_context(
                transcription,
                before=2,
                after=0,
            )

            print(f"📥 Transcript buffered: {transcription}")

        except Exception as error:
            print(f"Transcript buffering failed: {error}")
            return

        try:
            should_process = self.keyword_filter.should_process(transcription)

            print(f"🔎 Keyword detected: {should_process}")

        except Exception as error:
            print(f"Keyword detection failed: {error}")
            return

        if not should_process:
            return

        try:
            print("📋 Immediate context:")
            print(context)

            print("🤖 Sending immediate context to Gemini...")

            result = self.memory_engine.process(
                mode="immediate",
                text=context,
                current_time=datetime.now(),
            )

            print(f"🤖 Gemini result: {result!r}")

            memories = result["memories"]

            print(f"🧠 Memories extracted: {memories!r}")

        except Exception as error:
            # The transcription remains buffered for later processing.
            print(f"Immediate memory processing failed: {error}")
            return

        if not memories:
            return

        try:
            self.memory_manager.store_memories(memories)
            print("💾 Memories saved to database.")

        except Exception as error:
            # The transcription remains buffered even if persistence fails.
            print(f"Saving memories failed: {error}")