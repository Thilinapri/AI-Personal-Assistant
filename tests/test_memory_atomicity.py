import json
import tempfile
import threading
import unittest
from contextlib import contextmanager
from pathlib import Path

from src.database.database import Database
from src.memory.memory_manager import MemoryManager
from src.memory.retrieval_service import RetrievalService
from src.memory.rule_based_relationship_classifier import (
    RuleBasedRelationshipClassifier,
)


class FixedEmbedding:
    model_name = "mock-model"

    def encode(self, text):
        return [1.0, 0.0]


def make_memory(title="A fact", content="Some detail."):
    return {
        "category": "Note",
        "title": title,
        "content": content,
        "date": "",
        "time": "",
        "notification": False,
    }


class MemoryAtomicityTests(unittest.TestCase):
    def setUp(self):
        self.database = Database(":memory:")
        self.embedding = FixedEmbedding()
        self.manager = MemoryManager(
            self.database,
            embedding_service=self.embedding,
        )

    def tearDown(self):
        self.database.close()

    def test_embedding_generation_failure_precedes_any_insert(self):
        class BrokenEmbedding(FixedEmbedding):
            def encode(self, text):
                raise RuntimeError("embedding unavailable")

        manager = MemoryManager(self.database, embedding_service=BrokenEmbedding())
        self.assertEqual(manager.store_memories([make_memory()]), [])
        self.assertEqual(self.database.get_active_memories(), [])

    def test_memory_insert_failure_leaves_no_row(self):
        self.database.connection.execute("""
            CREATE TRIGGER fail_memory_insert BEFORE INSERT ON memories
            WHEN NEW.title = 'Fail insert'
            BEGIN SELECT RAISE(ABORT, 'injected insert failure'); END
        """)
        self.database.connection.commit()
        self.assertEqual(self.manager.store_memories([make_memory("Fail insert")]), [])
        self.assertEqual(self.database.get_active_memories(), [])

    def test_embedding_persistence_failure_rolls_back_insert(self):
        self.database.connection.execute("""
            CREATE TRIGGER fail_embedding_write BEFORE INSERT ON memories
            WHEN NEW.embedding IS NOT NULL
            BEGIN SELECT RAISE(ABORT, 'injected embedding write failure'); END
        """)
        self.database.connection.commit()
        self.assertEqual(self.manager.store_memories([make_memory()]), [])
        self.assertEqual(self.database.get_active_memories(), [])

    def test_memory_and_embedding_persist_together(self):
        self.assertEqual(len(self.manager.store_memories([make_memory()])), 1)
        row = self.database.get_active_memories()[0]
        self.assertEqual(json.loads(row[14]), [1.0, 0.0])
        self.assertEqual(row[15], self.embedding.model_name)

    def test_retry_after_failed_batch_does_not_duplicate_or_inflate_seen(self):
        self.database.connection.execute("""
            CREATE TRIGGER fail_second BEFORE INSERT ON memories
            WHEN NEW.title = 'Second'
            BEGIN SELECT RAISE(ABORT, 'injected second insert failure'); END
        """)
        self.database.connection.commit()
        batch = [make_memory("First"), make_memory("Second")]
        self.assertEqual(self.manager.store_memories(batch), [])
        self.assertEqual(self.database.get_active_memories(), [])

        self.database.connection.execute("DROP TRIGGER fail_second")
        self.database.connection.commit()
        self.assertEqual(len(self.manager.store_memories(batch)), 2)
        rows = self.database.get_active_memories()
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row[12] == 1 for row in rows))

    def test_identical_fields_are_not_merged_without_classifier_decision(self):
        same = make_memory()
        self.assertEqual(len(self.manager.store_memories([same])), 1)
        self.assertEqual(len(self.manager.store_memories([same])), 1)
        rows = self.database.get_active_memories()
        self.assertEqual(len(rows), 2)
        self.assertEqual([row[12] for row in rows], [1, 1])

    def test_relationship_classifier_duplicate_still_increments_seen(self):
        retrieval = RetrievalService(self.database, self.embedding)
        manager = MemoryManager(
            self.database,
            embedding_service=self.embedding,
            retrieval_service=retrieval,
            relationship_classifier=RuleBasedRelationshipClassifier(),
            candidate_threshold=0.0,
        )
        memory = make_memory("Same fact", "Same persisted observation.")
        manager.store_memory(memory)
        manager.store_memory(memory)
        rows = self.database.get_active_memories()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][12], 2)

    def test_duplicate_seen_increment_rolls_back_with_later_write_failure(self):
        retrieval = RetrievalService(self.database, self.embedding)
        manager = MemoryManager(
            self.database,
            embedding_service=self.embedding,
            retrieval_service=retrieval,
            relationship_classifier=RuleBasedRelationshipClassifier(),
            candidate_threshold=0.0,
        )
        existing = make_memory("Repeated observation", "Original wording.")
        existing_id = manager.store_memory(existing)
        initial = self.database.get_memory(existing_id)
        self.assertEqual(initial[12], 1)

        self.database.connection.execute("""
            CREATE TRIGGER fail_later_memory BEFORE INSERT ON memories
            WHEN NEW.title = 'Fail later'
            BEGIN SELECT RAISE(ABORT, 'injected later write failure'); END
        """)
        self.database.connection.commit()
        batch = [
            make_memory("Repeated observation", "A repeated observation."),
            make_memory("Fail later", "Force the second row to fail."),
        ]

        self.assertEqual(manager.store_memories(batch), [])
        rows_after_failure = self.database.get_active_memories()
        self.assertEqual(len(rows_after_failure), 1)
        self.assertEqual(rows_after_failure[0][0], existing_id)
        self.assertEqual(rows_after_failure[0][12], 1)
        self.assertEqual(json.loads(rows_after_failure[0][14]), [1.0, 0.0])
        self.assertEqual(rows_after_failure[0][15], self.embedding.model_name)

        self.database.connection.execute("DROP TRIGGER fail_later_memory")
        self.database.connection.commit()
        retry_ids = manager.store_memories(batch)

        self.assertEqual(len(retry_ids), 2)
        rows_after_retry = self.database.get_active_memories()
        self.assertEqual(len(rows_after_retry), 2)
        original_after_retry = self.database.get_memory(existing_id)
        self.assertEqual(original_after_retry[12], 2)
        new_row = next(row for row in rows_after_retry if row[0] != existing_id)
        self.assertEqual(new_row[2], "Fail later")
        self.assertEqual(json.loads(new_row[14]), [1.0, 0.0])
        self.assertEqual(new_row[15], self.embedding.model_name)

    def test_two_managers_serialize_writes_on_separate_sqlite_connections(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
            database_path = Path(directory) / "concurrent-memories.sqlite"
            first_database = Database(database_path)
            second_database = Database(database_path)
            self.addCleanup(first_database.close)
            self.addCleanup(second_database.close)

            embeddings_ready = threading.Barrier(2)
            first_acquired = threading.Event()
            second_begin_attempted = threading.Event()
            release_first = threading.Event()
            events = []
            event_lock = threading.Lock()
            errors = []
            second_acquired_before_release = []

            class SimultaneousEmbedding(FixedEmbedding):
                def encode(self, text):
                    embeddings_ready.wait(timeout=5)
                    return [1.0, 0.0]

            original_first_transaction = first_database.memory_write_transaction
            original_second_transaction = second_database.memory_write_transaction

            @contextmanager
            def hold_first_transaction():
                with original_first_transaction():
                    first_acquired.set()
                    if not second_begin_attempted.wait(timeout=5):
                        raise TimeoutError("second writer did not attempt BEGIN IMMEDIATE")
                    if not release_first.wait(timeout=5):
                        raise TimeoutError("first writer release timed out")
                    yield

            @contextmanager
            def observe_second_transaction():
                if not first_acquired.wait(timeout=5):
                    raise TimeoutError("first writer did not acquire its transaction")
                with original_second_transaction():
                    with event_lock:
                        events.append("second_acquired")
                        if not release_first.is_set():
                            second_acquired_before_release.append(True)
                    yield

            first_database.memory_write_transaction = hold_first_transaction
            second_database.memory_write_transaction = observe_second_transaction

            def trace_second_connection(statement):
                if statement.strip().upper().startswith("BEGIN IMMEDIATE"):
                    second_begin_attempted.set()

            second_database.connection.set_trace_callback(trace_second_connection)

            managers = [
                MemoryManager(first_database, embedding_service=SimultaneousEmbedding()),
                MemoryManager(second_database, embedding_service=SimultaneousEmbedding()),
            ]

            def store(manager, memory):
                try:
                    manager.store_memory(memory)
                except Exception as error:
                    errors.append(error)

            threads = [
                threading.Thread(
                    target=store,
                    args=(managers[0], make_memory("First connection")),
                ),
                threading.Thread(
                    target=store,
                    args=(managers[1], make_memory("Second connection")),
                ),
            ]
            try:
                for thread in threads:
                    thread.start()
                self.assertTrue(first_acquired.wait(timeout=5))
                self.assertTrue(second_begin_attempted.wait(timeout=5))
                release_first.set()
                for thread in threads:
                    thread.join(timeout=10)

                self.assertFalse(any(thread.is_alive() for thread in threads))
                self.assertEqual(errors, [])
                self.assertEqual(second_acquired_before_release, [])
                self.assertEqual(events, ["second_acquired"])

                rows = first_database.get_active_memories()
                self.assertEqual(
                    {row[2] for row in rows},
                    {"First connection", "Second connection"},
                )
                self.assertTrue(
                    all(json.loads(row[14]) == [1.0, 0.0] for row in rows)
                )
                self.assertTrue(
                    all(row[15] == "mock-model" for row in rows)
                )
            finally:
                release_first.set()
                for thread in threads:
                    if thread.is_alive():
                        thread.join(timeout=5)
                first_database.close()
                second_database.close()
        barrier = threading.Barrier(2)

        class SimultaneousEmbedding(FixedEmbedding):
            def encode(self, text):
                barrier.wait(timeout=5)
                return [1.0, 0.0]

        # Separate managers share the application's Database connection;
        # BEGIN IMMEDIATE plus the DB-level RLock guards their full decision/write.
        managers = [
            MemoryManager(self.database, embedding_service=SimultaneousEmbedding())
            for _ in range(2)
        ]
        errors = []

        def store(manager, memory):
            try:
                manager.store_memory(memory)
            except Exception as error:
                errors.append(error)

        threads = [
            threading.Thread(target=store, args=(managers[0], make_memory("One"))),
            threading.Thread(target=store, args=(managers[1], make_memory("Two"))),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(errors, [])
        rows = self.database.get_active_memories()
        self.assertEqual({row[2] for row in rows}, {"One", "Two"})
        self.assertTrue(all(json.loads(row[14]) == [1.0, 0.0] for row in rows))


if __name__ == "__main__":
    unittest.main()
