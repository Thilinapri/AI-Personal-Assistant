import io
import queue
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from src.audio.microphone import Microphone
from src.config import BLOCK_SIZE
from src.database.database import Database
from src.memory.memory_manager import MemoryManager
from src.memory.retrieval_service import RetrievalService
from src.memory.rule_based_relationship_classifier import (
    RuleBasedRelationshipClassifier,
)
from src.worker.audio_chunker import AudioChunker
from src.worker.audio_worker import AudioWorker


class FakeDatabase:
    def get_listening_enabled(self):
        return True


class RecoveringMicrophone:
    def __init__(self, failures=1):
        self.failures = failures
        self.read_count = 0
        self.start_count = 0
        self.stop_count = 0
        self.running = False

    def start(self):
        if self.running:
            raise AssertionError("duplicate microphone start")
        self.start_count += 1
        self.running = True

    def stop(self):
        self.stop_count += 1
        self.running = False

    def read(self):
        if not self.running:
            raise RuntimeError("microphone is stopped")
        self.read_count += 1
        if self.read_count <= self.failures:
            raise OSError("temporary capture error")
        return np.zeros((BLOCK_SIZE, 1), dtype=np.float32)


class StopAfterChunkQueue:
    def __init__(self):
        self.chunker = None
        self.items = []

    def put_nowait(self, item):
        self.items.append(item)
        self.chunker.stop()


class FakeTranscriptBuffer:
    def __init__(self):
        self.next_id = 0
        self.removed = []
        self.entries = []

    def add_with_context(self, text, before=2, after=0):
        self.next_id += 1
        self.entries.append((self.next_id, text))
        return self.next_id, [text]

    def remove(self, entry_id):
        self.removed.append(entry_id)


class SequenceTranscriber:
    def __init__(self, errors=()):
        self.errors = set(errors)
        self.calls = 0

    def transcribe(self, audio):
        self.calls += 1
        if self.calls in self.errors:
            raise RuntimeError("mock transcription failure")
        return f"Remember item {self.calls}."


class AlwaysKeyword:
    def should_process(self, text):
        return "remember" in text.lower()


class SequenceMemoryEngine:
    def __init__(self, errors=(), return_memories=True):
        self.errors = set(errors)
        self.return_memories = return_memories
        self.calls = 0

    def process(self, **kwargs):
        self.calls += 1
        if self.calls in self.errors:
            raise RuntimeError("mock memory extraction failure")
        memories = []
        if self.return_memories:
            memories = [{
                "category": "Note",
                "title": f"memory-{self.calls}",
                "content": f"content-{self.calls}",
                "date": "",
                "time": "",
                "notification": False,
            }]
        return {"memories": memories}


class TwoMemoryEngine:
    def __init__(self, memories):
        self.memories = memories

    def process(self, **kwargs):
        return {"memories": self.memories}


class FixedEmbeddingService:
    model_name = "test-fixed-embedding"

    def encode(self, text):
        return [1.0, 0.0]


class FailSecondEncodingOnce(FixedEmbeddingService):
    def __init__(self):
        self.calls = 0

    def encode(self, text):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("injected embedding generation failure")
        return [1.0, 0.0]


class FailSecondMemoryInsertOnce:
    """Proxy that fails the second distinct record on its first insert."""

    def __init__(self, database, failing_title):
        self.database = database
        self.failing_title = failing_title
        self.failed = False

    def __getattr__(self, name):
        return getattr(self.database, name)

    def insert_memory(self, memory, *args, **kwargs):
        if memory["title"] == self.failing_title and not self.failed:
            self.failed = True
            raise RuntimeError("injected one-time insert failure")
        return self.database.insert_memory(memory, *args, **kwargs)


class FakeMemoryManager:
    def __init__(self, errors=()):
        self.errors = set(errors)
        self.calls = 0
        self.stored = []

    def store_memories(self, memories):
        self.calls += 1
        if self.calls in self.errors:
            # Mirrors MemoryManager.store_memories(), which returns fewer IDs
            # after it catches a per-memory storage error.
            return []
        self.stored.extend(memories)
        return list(range(len(self.stored) - len(memories) + 1, len(self.stored) + 1))


def make_worker(audio_queue, transcriber, memory_engine, memory_manager):
    return AudioWorker(
        audio_queue=audio_queue,
        stt_service=transcriber,
        transcript_buffer=FakeTranscriptBuffer(),
        keyword_filter=AlwaysKeyword(),
        memory_engine=memory_engine,
        memory_manager=memory_manager,
    )


class AudioWorkerContinuityTests(unittest.TestCase):
    def run_worker(self, worker, chunks):
        audio_queue = worker.audio_queue
        for chunk in chunks:
            audio_queue.put(chunk)
        audio_queue.put(None)
        with redirect_stdout(io.StringIO()):
            worker.run()
        self.assertEqual(audio_queue.unfinished_tasks, 0)

    def test_ten_consecutive_keyword_chunks_are_processed_and_stored(self):
        audio_queue = queue.Queue()
        transcriber = SequenceTranscriber()
        engine = SequenceMemoryEngine()
        manager = FakeMemoryManager()
        worker = make_worker(audio_queue, transcriber, engine, manager)

        self.run_worker(worker, [b"chunk"] * 10)

        self.assertEqual(transcriber.calls, 10)
        self.assertEqual(engine.calls, 10)
        self.assertEqual(manager.calls, 10)
        self.assertEqual(len(manager.stored), 10)

    def test_extracted_memory_reaches_existing_local_database(self):
        database = Database(":memory:")
        self.addCleanup(database.close)
        audio_queue = queue.Queue()
        transcriber = SequenceTranscriber()
        worker = AudioWorker(
            audio_queue=audio_queue,
            stt_service=transcriber,
            transcript_buffer=FakeTranscriptBuffer(),
            keyword_filter=AlwaysKeyword(),
            memory_engine=SequenceMemoryEngine(),
            memory_manager=MemoryManager(database=database),
        )

        self.run_worker(worker, [b"chunk"])

        rows = database.get_all_memories()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][2], "memory-1")

    def test_partial_save_retry_does_not_duplicate_first_memory(self):
        database = Database(":memory:")
        self.addCleanup(database.close)
        database_proxy = FailSecondMemoryInsertOnce(
            database,
            failing_title="Second memory",
        )
        embeddings = FixedEmbeddingService()
        manager = MemoryManager(
            database=database_proxy,
            embedding_service=embeddings,
            retrieval_service=RetrievalService(
                database=database_proxy,
                embedding_service=embeddings,
            ),
            relationship_classifier=RuleBasedRelationshipClassifier(),
        )
        memories = [
            {
                "category": "Note",
                "title": "First memory",
                "content": "First extracted fact.",
                "date": "",
                "time": "",
                "notification": False,
            },
            {
                "category": "Task",
                "title": "Second memory",
                "content": "Second extracted fact.",
                "date": "",
                "time": "",
                "notification": False,
            },
        ]
        audio_queue = queue.Queue()
        transcript_buffer = FakeTranscriptBuffer()
        worker = AudioWorker(
            audio_queue=audio_queue,
            stt_service=SequenceTranscriber(),
            transcript_buffer=transcript_buffer,
            keyword_filter=AlwaysKeyword(),
            memory_engine=TwoMemoryEngine(memories),
            memory_manager=manager,
        )

        self.run_worker(worker, [b"original chunk", b"retry chunk"])

        rows = database.get_active_memories()
        rows_by_title = {row[2]: row for row in rows}
        self.assertEqual(set(rows_by_title), {"First memory", "Second memory"})
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows_by_title["First memory"][12], 1)
        self.assertEqual(rows_by_title["Second memory"][12], 1)
        self.assertEqual(transcript_buffer.removed, [2])

    def test_embedding_failure_then_retry_does_not_inflate_seen_count(self):
        database = Database(":memory:")
        self.addCleanup(database.close)
        embeddings = FailSecondEncodingOnce()
        manager = MemoryManager(
            database=database,
            embedding_service=embeddings,
            retrieval_service=RetrievalService(
                database=database,
                embedding_service=embeddings,
            ),
            relationship_classifier=RuleBasedRelationshipClassifier(),
        )
        memory = {
            "category": "Note",
            "title": "Power outage plan",
            "content": "Keep a charged backup battery.",
            "date": "",
            "time": "",
            "notification": False,
        }

        with redirect_stdout(io.StringIO()):
            first_result = manager.store_memories([memory])
            retry_result = manager.store_memories([memory])

        rows = database.get_active_memories()
        self.assertEqual(first_result, [])
        self.assertEqual(len(retry_result), 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][2], memory["title"])
        self.assertEqual(rows[0][12], 1)

    def test_extraction_failure_does_not_block_next_keyword_chunk(self):
        audio_queue = queue.Queue()
        transcriber = SequenceTranscriber()
        engine = SequenceMemoryEngine(errors={1})
        manager = FakeMemoryManager()
        worker = make_worker(audio_queue, transcriber, engine, manager)

        self.run_worker(worker, [b"first", b"second"])

        self.assertEqual(transcriber.calls, 2)
        self.assertEqual(engine.calls, 2)
        self.assertEqual(
            [memory["title"] for memory in manager.stored],
            ["memory-2"],
        )
        self.assertEqual(worker.transcript_buffer.removed, [2])

    def test_transcription_failure_does_not_block_next_chunk(self):
        audio_queue = queue.Queue()
        transcriber = SequenceTranscriber(errors={1})
        engine = SequenceMemoryEngine()
        manager = FakeMemoryManager()
        worker = make_worker(audio_queue, transcriber, engine, manager)

        self.run_worker(worker, [b"failed", b"next"])

        self.assertEqual(transcriber.calls, 2)
        self.assertEqual(engine.calls, 1)
        self.assertEqual(len(manager.stored), 1)

    def test_storage_failure_does_not_block_next_chunk(self):
        audio_queue = queue.Queue()
        transcriber = SequenceTranscriber()
        engine = SequenceMemoryEngine()
        manager = FakeMemoryManager(errors={1})
        worker = make_worker(audio_queue, transcriber, engine, manager)

        self.run_worker(worker, [b"first", b"second"])

        self.assertEqual(transcriber.calls, 2)
        self.assertEqual(engine.calls, 2)
        self.assertEqual(manager.calls, 2)
        self.assertEqual(
            [memory["title"] for memory in manager.stored],
            ["memory-2"],
        )
        self.assertEqual(worker.transcript_buffer.removed, [2])

    def test_no_memory_result_does_not_stop_worker(self):
        audio_queue = queue.Queue()
        transcriber = SequenceTranscriber()
        engine = SequenceMemoryEngine(return_memories=False)
        manager = FakeMemoryManager()
        worker = make_worker(audio_queue, transcriber, engine, manager)

        self.run_worker(worker, [b"one", b"two", b"three"])

        self.assertEqual(transcriber.calls, 3)
        self.assertEqual(engine.calls, 3)
        self.assertEqual(manager.calls, 0)


class AudioChunkerRecoveryTests(unittest.TestCase):
    def make_chunker(self, microphone):
        audio_queue = StopAfterChunkQueue()
        chunker = AudioChunker(microphone, audio_queue, FakeDatabase())
        audio_queue.chunker = chunker
        # Avoid sleeping in recovery tests; production uses bounded backoff.
        chunker._stop_event.wait = lambda timeout: False
        return chunker, audio_queue

    def test_transient_microphone_error_recovers_and_emits_chunk(self):
        microphone = RecoveringMicrophone(failures=1)
        microphone.start()
        chunker, audio_queue = self.make_chunker(microphone)

        with redirect_stdout(io.StringIO()):
            chunker._run()

        self.assertEqual(len(audio_queue.items), 1)
        self.assertEqual(audio_queue.items[0].shape, (20 * 16000,))
        self.assertEqual(microphone.start_count, 2)
        self.assertEqual(microphone.stop_count, 1)

    def test_permanent_microphone_error_stops_after_bounded_retries(self):
        microphone = RecoveringMicrophone(failures=100)
        microphone.start()
        chunker, audio_queue = self.make_chunker(microphone)

        with redirect_stdout(io.StringIO()):
            chunker._run()

        self.assertEqual(audio_queue.items, [])
        self.assertEqual(
            microphone.start_count,
            1 + chunker.MAX_CAPTURE_RECOVERY_ATTEMPTS,
        )
        self.assertFalse(microphone.running)


class MicrophoneLifecycleTests(unittest.TestCase):
    def make_microphone(self, stream_factory):
        import src.audio.microphone as microphone_module

        patches = (
            patch.object(
                microphone_module.sd,
                "default",
                SimpleNamespace(device=(0, None)),
            ),
            patch.object(
                microphone_module.sd,
                "query_devices",
                return_value={"max_input_channels": 1, "name": "mock"},
            ),
            patch.object(microphone_module.sd, "InputStream", side_effect=stream_factory),
        )
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        return Microphone()

    def test_start_failure_closes_partial_stream_and_can_retry(self):
        streams = []

        class Stream:
            def __init__(self, fail_start=False):
                self.fail_start = fail_start
                self.closed = False
                streams.append(self)

            def start(self):
                if self.fail_start:
                    raise OSError("mock device unavailable")

            def close(self):
                self.closed = True

        mic = self.make_microphone(
            lambda **kwargs: Stream(fail_start=len(streams) == 0)
        )

        with self.assertRaises(OSError):
            mic.start()
        self.assertTrue(streams[0].closed)
        self.assertIsNone(mic.stream)

        mic.start()
        self.assertIs(mic.stream, streams[1])

    def test_stop_closes_and_clears_stream_even_if_stop_raises(self):
        class Stream:
            closed = False

            def start(self):
                pass

            def stop(self):
                raise OSError("mock stop error")

            def close(self):
                self.closed = True

        stream = Stream()
        mic = self.make_microphone(lambda **kwargs: stream)
        mic.start()

        with self.assertRaises(OSError):
            mic.stop()

        self.assertTrue(stream.closed)
        self.assertIsNone(mic.stream)


if __name__ == "__main__":
    unittest.main()
