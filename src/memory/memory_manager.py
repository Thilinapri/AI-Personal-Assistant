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
        """Store multiple memories without one failure stopping the batch."""

        if not memories:
            return []

        stored_ids = []

        for memory in memories:

            try:
                memory_id = self.store_memory(memory)
                stored_ids.append(memory_id)

            except Exception as error:
                title = memory.get(
                    "title",
                    "Unknown memory",
                )

                print(
                    f"Memory processing failed "
                    f"for '{title}': {error}"
                )

        return stored_ids

    def store_memory(self, memory):
        """Store one memory after checking for duplicates or updates."""

        candidates = self._find_candidates(memory)

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
                return candidate["id"]

            # ---------------------------------
            # Update
            # ---------------------------------

            if relationship == "update":

                old_memory_id = candidate["id"]

                memory_id = self.database.replace_memory(
                    old_memory_id,
                    memory,
                )

                self._store_embedding(
                    memory_id,
                    memory,
                )

                if self.reminder_manager is not None:

                    # Cancel reminder belonging to old information.
                    self.reminder_manager.cancel_for_memory(
                        old_memory_id
                    )

                    # Create reminder for the updated memory.
                    self.reminder_manager.create_for_memory(
                        memory_id,
                        memory,
                    )

                return memory_id

            # ---------------------------------
            # Related
            # ---------------------------------

            if relationship == "related":
                break

        # ---------------------------------
        # New or Related Memory
        # ---------------------------------

        memory_id = self.database.insert_memory(memory)

        self._store_embedding(
            memory_id,
            memory,
        )

        if self.reminder_manager is not None:

            self.reminder_manager.create_for_memory(
                memory_id,
                memory,
            )

        return memory_id

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

    def _find_candidates(self, memory):
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