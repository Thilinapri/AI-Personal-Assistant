import json
import math
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SemanticPrivacyResult:
    probability: float
    decision: str
    cloud_safe: bool


class SemanticPrivacyClassifier:
    """
    Lightweight semantic privacy classifier.

    Uses embeddings produced by EchoMind's existing shared
    EmbeddingService. The classifier itself only performs a
    weighted sum and sigmoid calculation.
    """

    DEFAULT_MODEL_PATH = (
        Path(__file__).resolve().parent
        / "models"
        / "semantic_privacy_classifier.json"
    )

    SAFE = "SAFE"
    UNCERTAIN = "UNCERTAIN"
    SENSITIVE = "SENSITIVE"

    def __init__(
        self,
        embedding_service,
        model_path=None,
    ):

        if embedding_service is None:
            raise ValueError(
                "embedding_service is required."
            )

        self.embedding_service = (
            embedding_service
        )

        self.model_path = (
            Path(model_path)
            if model_path
            else self.DEFAULT_MODEL_PATH
        )

        self._load_model()

    def _load_model(self):

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Semantic privacy model not found: "
                f"{self.model_path}"
            )

        with self.model_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            model = json.load(file)

        self.embedding_model = model[
            "embedding_model"
        ]

        self.embedding_dimension = int(
            model["embedding_dimension"]
        )

        self.weights = tuple(
            float(value)
            for value in model["weights"]
        )

        self.bias = float(
            model["bias"]
        )

        self.safe_threshold = float(
            model["safe_threshold"]
        )

        self.sensitive_threshold = float(
            model["sensitive_threshold"]
        )

        if len(self.weights) != (
            self.embedding_dimension
        ):
            raise ValueError(
                "Classifier weight count does not "
                "match embedding dimension."
            )

        if not (
            0.0
            <= self.safe_threshold
            < self.sensitive_threshold
            <= 1.0
        ):
            raise ValueError(
                "Invalid semantic privacy thresholds."
            )

        service_model_name = getattr(
            self.embedding_service,
            "model_name",
            None,
        )

        if (
            service_model_name is not None
            and service_model_name
            != self.embedding_model
        ):
            raise ValueError(
                "Embedding model does not match "
                "semantic privacy classifier."
            )

    @staticmethod
    def _sigmoid(value):

        if value >= 0:
            return 1.0 / (
                1.0 + math.exp(-value)
            )

        exp_value = math.exp(value)

        return exp_value / (
            1.0 + exp_value
        )

    def classify_embedding(
        self,
        embedding,
    ):

        if embedding is None:
            raise ValueError(
                "Embedding cannot be None."
            )

        if len(embedding) != (
            self.embedding_dimension
        ):
            raise ValueError(
                "Embedding dimension does not "
                "match classifier."
            )

        logit = self.bias

        for weight, value in zip(
            self.weights,
            embedding,
        ):
            logit += (
                weight * float(value)
            )

        probability = self._sigmoid(
            logit
        )

        if probability < (
            self.safe_threshold
        ):
            decision = self.SAFE
            cloud_safe = True

        elif probability < (
            self.sensitive_threshold
        ):
            decision = self.UNCERTAIN
            cloud_safe = False

        else:
            decision = self.SENSITIVE
            cloud_safe = False

        return SemanticPrivacyResult(
            probability=probability,
            decision=decision,
            cloud_safe=cloud_safe,
        )

    def classify(
        self,
        text,
    ):

        embedding = (
            self.embedding_service.encode(
                text
            )
        )

        return self.classify_embedding(
            embedding
        )

    def classify_many(
        self,
        texts,
    ):

        embeddings = (
            self.embedding_service.encode_many(
                texts
            )
        )

        return [
            self.classify_embedding(
                embedding
            )
            for embedding in embeddings
        ]