from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Creates semantic embeddings for memory text."""

    DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(self, model_name=None):

        self.model_name = model_name or self.DEFAULT_MODEL

        print(f"Loading embedding model: {self.model_name}")

        self.model = SentenceTransformer(self.model_name)

        print("Embedding model loaded.")

    def encode(self, text):
        """Convert text into a normalized embedding vector."""

        if not text or not text.strip():
            raise ValueError("Text cannot be empty.")

        embedding = self.model.encode(
            text,
            normalize_embeddings=True
        )

        return embedding.tolist()