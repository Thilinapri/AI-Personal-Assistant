import json


class MemoryManager:
    """Coordinates long-term memory storage and management."""

    def __init__(
        self,
        database,
        embedding_service=None,
        retrieval_service=None,
        relationship_classifier=None,
        reminder_manager=None,
        candidate_threshold=0.72,
    ):
        self.database = database
        self.embedding_service = embedding_service
        self.retrieval_service = retrieval_service
        self.relationship_classifier = relationship_classifier
        self.reminder_manager = reminder_manager
        self.candidate_threshold = candidate_threshold

    def store_memories(self, memories):
        """Store a batch atomically so failures cannot leave partial retries."""

        if not memories:
            return []

        print(f"[DATABASE] Preparing {len(memories)} memory record(s).")
        try:
            prepared = [self._prepare_embedding(memory) for memory in memories]
        except Exception as error:
            print(
                "[DATABASE] Embedding preparation failed; "
                f"no memory rows written: {type(error).__name__}"
            )
            return []

        stored_ids = []
        reminder_actions = []
        try:
            # Embeddings are generated before the short write transaction.
            # BEGIN IMMEDIATE serializes candidate lookup and writes across
            # independent SQLite connections and processes.
            with self.database.memory_write_transaction():
                for memory, embedding_data in zip(memories, prepared):
                    memory_id, reminder_action = (
                        self._store_memory_in_transaction(
                            memory,
                            embedding_data,
                        )
                    )
                    stored_ids.append(memory_id)
                    if reminder_action is not None:
                        reminder_actions.append(reminder_action)
        except Exception as error:
            print(
                "[DATABASE] Memory batch rolled back: "
                f"{type(error).__name__}"
            )
            return []

        self._apply_reminder_actions(reminder_actions)
        print(
            "[DATABASE] Local transaction committed: "
            f"{len(stored_ids)}/{len(memories)} memory record(s)."
        )
        return stored_ids

    def store_memory(self, memory):
        """Store one memory atomically and return its existing or new ID."""

        stored_ids = self.store_memories([memory])
        if not stored_ids:
            raise RuntimeError("Memory and embedding transaction failed.")
        return stored_ids[0]

    def _store_memory_in_transaction(self, memory, embedding_data):
        """Classify and persist one memory inside a batch transaction."""

        candidates = self._find_candidates(
            memory,
            query_embedding=embedding_data["query_embedding"],
        )

        for candidate in candidates:

            relationship = self.relationship_classifier.classify(
                memory,
                candidate,
            )

            # ---------------------------------
            # Duplicate
            # ---------------------------------

            if relationship == "duplicate":

                self.database.increment_seen(
                    candidate["id"]
                )

                # Do not create another reminder.
                return candidate["id"], None

            # ---------------------------------
            # Update
            # ---------------------------------

            if relationship == "update":

                old_memory_id = candidate["id"]

                memory_id = self.database.replace_memory(
                    old_memory_id,
                    memory,
                    embedding=embedding_data["embedding"],
                    embedding_model=embedding_data["embedding_model"],
                )

                return memory_id, ("replace", old_memory_id, memory_id, memory)

            # ---------------------------------
            # Related
            # ---------------------------------

            if relationship == "related":
                break

        # ---------------------------------
        # New or Related Memory
        # ---------------------------------

        memory_id = self.database.insert_memory(
            memory,
            embedding=embedding_data["embedding"],
            embedding_model=embedding_data["embedding_model"],
        )
        return memory_id, ("create", None, memory_id, memory)

    def update_memory(self, memory_id, memory):
        """Update a user-edited memory and refresh related data."""

        try:
            embedding_data = self._prepare_embedding(memory)
            with self.database.memory_write_transaction():
                existing = self.database.get_memory(memory_id)
                if existing is None or existing[9] != "active":
                    return False
                serialized_embedding = embedding_data["embedding"]
                embedding_model = embedding_data["embedding_model"]
                if serialized_embedding is None:
                    serialized_embedding = existing[14]
                    embedding_model = existing[15]
                updated = self.database.update_memory(
                    memory_id,
                    memory,
                    embedding=serialized_embedding,
                    embedding_model=embedding_model,
                )
                if not updated:
                    return False
        except Exception as error:
            print(f"[DATABASE] Memory update rolled back: {type(error).__name__}")
            return False

        # Replace any old pending reminder.
        if self.reminder_manager is not None:

            self.reminder_manager.cancel_for_memory(
                memory_id
            )

            self.reminder_manager.create_for_memory(
                memory_id,
                memory,
            )

        return True

    def backfill_missing_embeddings(self):
        """Generate embeddings for active memories that do not have one yet."""

        if self.embedding_service is None:
            return 0

        memories = self.database.get_active_memories()

        updated_count = 0

        for memory in memories:

            embedding = memory[14]

            if embedding is not None:
                continue

            memory_data = {
                "category": memory[1],
                "title": memory[2],
                "content": memory[3],
                "date": memory[4],
                "time": memory[5],
            }

            self._store_embedding(
                memory[0],
                memory_data,
            )

            updated_count += 1

        return updated_count

    def _find_candidates(self, memory, query_embedding=None):
        """Find similar active memories stored locally."""

        if (
            self.retrieval_service is None
            or self.relationship_classifier is None
        ):
            return []

        memory_text = self._build_memory_text(memory)

        results = self.retrieval_service.search(
            memory_text,
            limit=3,
            query_embedding=query_embedding,
        )

        return [
            result
            for result in results
            if result["score"] >= self.candidate_threshold
        ]

    def _store_embedding(self, memory_id, memory):
        """Generate and store an embedding for a memory."""

        if self.embedding_service is None:
            return

        memory_text = self._build_memory_text(memory)

        embedding = self.embedding_service.encode(
            memory_text
        )

        self.database.update_embedding(
            memory_id,
            json.dumps(embedding),
            self.embedding_service.model_name,
        )

    def _prepare_embedding(self, memory):
        """Generate vectors and serialized payload before opening a transaction."""
        query_embedding = None
        embedding = None
        embedding_model = None
        memory_text = self._build_memory_text(memory)

        if self.retrieval_service is not None:
            query_service = self.retrieval_service.embedding_service
            query_embedding = query_service.encode(memory_text)
            if self.embedding_service is query_service:
                embedding = query_embedding
                embedding_model = query_service.model_name

        if self.embedding_service is not None and embedding is None:
            embedding = self.embedding_service.encode(memory_text)
            embedding_model = self.embedding_service.model_name

        return {
            "query_embedding": query_embedding,
            "embedding": json.dumps(embedding) if embedding is not None else None,
            "embedding_model": embedding_model,
        }

    def _apply_reminder_actions(self, actions):
        if self.reminder_manager is None:
            return
        for action, old_id, memory_id, memory in actions:
            try:
                if action == "replace":
                    self.reminder_manager.cancel_for_memory(old_id)
                self.reminder_manager.create_for_memory(memory_id, memory)
            except Exception as error:
                # Reminder failures must not misreport an already committed
                # memory transaction as failed and trigger duplicate retries.
                print(f"[REMINDER] Post-commit update failed: {type(error).__name__}")

    def _build_memory_text(self, memory):
        """Build one searchable text representation of a memory."""

        parts = [
            memory.get("category", ""),
            memory.get("title", ""),
            memory.get("content", ""),
            memory.get("date", ""),
            memory.get("time", ""),
        ]

        return " ".join(
            str(part).strip()
            for part in parts
            if part
        )
