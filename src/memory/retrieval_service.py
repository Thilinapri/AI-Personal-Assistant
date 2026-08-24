import json


class RetrievalService:
    """Finds stored memories that are semantically related to a query."""

    def __init__(self, database, embedding_service):
        self.database = database
        self.embedding_service = embedding_service

    def search(self, query, limit=5):
        """Return the most semantically relevant active memories."""

        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        query_embedding = self.embedding_service.encode(query)

        memories = self.database.get_active_memories()

        results = []

        for memory in memories:

            embedding_json = memory[14]
            embedding_model = memory[15]

            # Skip memories that do not have an embedding yet.
            if not embedding_json:
                continue

            # Do not compare vectors created by a different model.
            if embedding_model != self.embedding_service.model_name:
                continue

            memory_embedding = json.loads(embedding_json)

            similarity = self._cosine_similarity(
                query_embedding,
                memory_embedding
            )

            results.append({
                "id": memory[0],
                "category": memory[1],
                "title": memory[2],
                "content": memory[3],
                "date": memory[4],
                "time": memory[5],
                "score": similarity,
            })

        results.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return results[:limit]

    def _cosine_similarity(self, vector_a, vector_b):
        """Compare two normalized embedding vectors."""

        return sum(
            a * b
            for a, b in zip(vector_a, vector_b)
        )