import json


class MemoryManager:
    """Coordinates long-term memory storage and management."""

    def __init__(self, database, embedding_service=None):

        self.database = database
        self.embedding_service = embedding_service

    def store_memories(self, memories):
        """Store memories and generate embeddings when available."""

        if not memories:
            return

        for memory in memories:

            memory_id = self.database.insert_memory(memory)

            if self.embedding_service is not None:

                memory_text = self._build_memory_text(memory)

                embedding = self.embedding_service.encode(memory_text)

                self.database.update_embedding(
                    memory_id,
                    json.dumps(embedding),
                    self.embedding_service.model_name,
                )

    def _build_memory_text(self, memory):
        """Create one text representation of a memory for embedding."""

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