import queue
import unittest
from contextlib import redirect_stdout
from io import StringIO

from src.worker.audio_worker import AudioWorker
from src.worker.session_processor import SessionProcessor


class FakeMemoryEngine:

    def __init__(self, result):
        self.result = result
        self.calls = []

    def process(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


class FakeWhisper:

    def transcribe(self, audio):
        return "Remind me about the meeting tomorrow."


class FakeKeywordFilter:

    def should_process(self, text):
        return True


class FakeAudioTranscriptBuffer:

    def add_with_context(
        self,
        text,
        before=2,
        after=0,
    ):
        return (
            3,
            [
                "We discussed the project.",
                "The meeting is tomorrow.",
                text,
            ],
        )

    def remove(self, entry_id):
        pass


class FakeSessionTranscriptBuffer:

    def __init__(self):
        self.cleared_through = None

    def snapshot(self):
        return {
            "entries": [
                {
                    "id": 1,
                    "text": "We discussed the project.",
                },
                {
                    "id": 2,
                    "text": "The meeting is tomorrow.",
                },
            ],
            "last_entry_id": 2,
        }

    def clear_through(self, entry_id):
        self.cleared_through = entry_id


class FakeMemoryManager:

    def store_memories(self, memories):
        return list(range(len(memories)))


class SequencedMemoryEngine:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def process(self, **kwargs):
        self.calls.append(kwargs)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class PartialMemoryManager:
    def __init__(self, stored_count):
        self.stored_count = stored_count

    def store_memories(self, memories):
        return list(range(min(self.stored_count, len(memories))))


class WorkerSentenceInterfaceTests(
    unittest.TestCase
):

    def test_audio_worker_passes_sentence_list_to_memory_engine(
        self,
    ):

        memory_engine = FakeMemoryEngine(
            {
                "memories": [],
            }
        )

        worker = AudioWorker(
            audio_queue=queue.Queue(),
            stt_service=FakeWhisper(),
            transcript_buffer=(
                FakeAudioTranscriptBuffer()
            ),
            keyword_filter=FakeKeywordFilter(),
            memory_engine=memory_engine,
            memory_manager=FakeMemoryManager(),
        )

        worker.process_audio(
            b"fake-audio"
        )

        self.assertEqual(
            len(memory_engine.calls),
            1,
        )

        call = memory_engine.calls[0]

        self.assertEqual(
            call["mode"],
            "immediate",
        )

        self.assertEqual(
            call["sentences"],
            [
                "We discussed the project.",
                "The meeting is tomorrow.",
                (
                    "Remind me about the meeting "
                    "tomorrow."
                ),
            ],
        )

        self.assertNotIn(
            "text",
            call,
        )


    def test_session_processor_passes_sentence_list_to_memory_engine(
        self,
    ):

        transcript_buffer = (
            FakeSessionTranscriptBuffer()
        )

        memory_engine = FakeMemoryEngine(
            {
                "summary": "Project discussion.",
                "memories": [],
            }
        )

        processor = SessionProcessor(
            transcript_buffer=transcript_buffer,
            memory_engine=memory_engine,
            memory_manager=FakeMemoryManager(),
        )

        result = (
            processor.process_current_session()
        )

        self.assertTrue(
            result
        )

        self.assertEqual(
            len(memory_engine.calls),
            1,
        )

        call = memory_engine.calls[0]

        self.assertEqual(
            call["mode"],
            "summary",
        )

        self.assertEqual(
            call["sentences"],
            [
                "We discussed the project.",
                "The meeting is tomorrow.",
            ],
        )

        self.assertNotIn(
            "text",
            call,
        )

        self.assertEqual(
            transcript_buffer.cleared_through,
            2,
        )

    def test_session_failure_retains_transcript_and_next_cycle_recovers(self):
        transcript_buffer = FakeSessionTranscriptBuffer()
        memory_engine = SequencedMemoryEngine([
            RuntimeError("temporary provider failure"),
            {
                "summary": "private summary text",
                "memories": [],
            },
        ])
        processor = SessionProcessor(
            transcript_buffer=transcript_buffer,
            memory_engine=memory_engine,
            memory_manager=FakeMemoryManager(),
        )
        output = StringIO()

        with redirect_stdout(output):
            first_result = processor.process_current_session()
            self.assertIsNone(transcript_buffer.cleared_through)
            second_result = processor.process_current_session()

        self.assertFalse(first_result)
        self.assertTrue(second_result)
        self.assertEqual(len(memory_engine.calls), 2)
        self.assertEqual(transcript_buffer.cleared_through, 2)
        self.assertNotIn("private summary text", output.getvalue())

    def test_session_partial_storage_failure_retains_snapshot(self):
        transcript_buffer = FakeSessionTranscriptBuffer()
        memory = {
            "category": "Note",
            "title": "Meeting",
            "content": "Meeting details.",
            "date": "",
            "time": "",
            "notification": False,
        }
        processor = SessionProcessor(
            transcript_buffer=transcript_buffer,
            memory_engine=SequencedMemoryEngine([
                {
                    "summary": "summary",
                    "memories": [memory, memory],
                }
            ]),
            memory_manager=PartialMemoryManager(stored_count=1),
        )

        with redirect_stdout(StringIO()):
            result = processor.process_current_session()

        self.assertFalse(result)
        self.assertIsNone(transcript_buffer.cleared_through)

    def test_session_processor_skips_concurrent_snapshot_cycle(self):
        transcript_buffer = FakeSessionTranscriptBuffer()
        memory_engine = FakeMemoryEngine({
            "summary": "summary",
            "memories": [],
        })
        processor = SessionProcessor(
            transcript_buffer=transcript_buffer,
            memory_engine=memory_engine,
            memory_manager=FakeMemoryManager(),
        )
        processor._process_lock.acquire()
        try:
            with redirect_stdout(StringIO()):
                result = processor.process_current_session()
        finally:
            processor._process_lock.release()

        self.assertFalse(result)
        self.assertEqual(memory_engine.calls, [])
        self.assertIsNone(transcript_buffer.cleared_through)


if __name__ == "__main__":
    unittest.main()
