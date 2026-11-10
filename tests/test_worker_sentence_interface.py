import queue
import unittest

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
        pass


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
            whisper=FakeWhisper(),
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


if __name__ == "__main__":
    unittest.main()