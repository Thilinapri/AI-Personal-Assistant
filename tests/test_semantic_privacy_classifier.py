import json
import tempfile
import unittest
from pathlib import Path

from src.privacy.semantic_privacy_classifier import (
    SemanticPrivacyClassifier,
)


class FakeEmbeddingService:

    model_name = "fake-model"

    EMBEDDINGS = {
        "safe": [-1.0, 0.0],
        "uncertain": [0.0, 0.0],
        "sensitive": [1.0, 0.0],
    }

    def encode(self, text):
        return self.EMBEDDINGS[text]

    def encode_many(self, texts):
        return [
            self.encode(text)
            for text in texts
        ]


class SemanticPrivacyClassifierTests(
    unittest.TestCase
):

    def setUp(self):

        self.temp_directory = (
            tempfile.TemporaryDirectory()
        )

        self.model_path = (
            Path(self.temp_directory.name)
            / "model.json"
        )

        model = {
            "embedding_model": "fake-model",
            "embedding_dimension": 2,
            "weights": [1.0, 0.0],
            "bias": 0.0,
            "safe_threshold": 0.45,
            "sensitive_threshold": 0.55,
        }

        with self.model_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                model,
                file,
            )

        self.embedding_service = (
            FakeEmbeddingService()
        )

        self.classifier = (
            SemanticPrivacyClassifier(
                embedding_service=(
                    self.embedding_service
                ),
                model_path=self.model_path,
            )
        )

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_safe_result_is_cloud_safe(self):

        result = self.classifier.classify(
            "safe"
        )

        self.assertEqual(
            result.decision,
            "SAFE",
        )

        self.assertTrue(
            result.cloud_safe
        )

        self.assertLess(
            result.probability,
            0.45,
        )

    def test_uncertain_result_fails_closed(self):

        result = self.classifier.classify(
            "uncertain"
        )

        self.assertEqual(
            result.decision,
            "UNCERTAIN",
        )

        self.assertFalse(
            result.cloud_safe
        )

        self.assertGreaterEqual(
            result.probability,
            0.45,
        )

        self.assertLess(
            result.probability,
            0.55,
        )

    def test_sensitive_result_is_not_cloud_safe(self):

        result = self.classifier.classify(
            "sensitive"
        )

        self.assertEqual(
            result.decision,
            "SENSITIVE",
        )

        self.assertFalse(
            result.cloud_safe
        )

        self.assertGreaterEqual(
            result.probability,
            0.55,
        )

    def test_classify_many_preserves_order(self):

        results = self.classifier.classify_many(
            [
                "safe",
                "uncertain",
                "sensitive",
            ]
        )

        decisions = [
            result.decision
            for result in results
        ]

        self.assertEqual(
            decisions,
            [
                "SAFE",
                "UNCERTAIN",
                "SENSITIVE",
            ],
        )

    def test_wrong_embedding_dimension_is_rejected(self):

        with self.assertRaises(
            ValueError
        ):
            self.classifier.classify_embedding(
                [1.0]
            )

    def test_embedding_model_mismatch_is_rejected(self):

        class WrongEmbeddingService:
            model_name = "wrong-model"

        with self.assertRaises(
            ValueError
        ):
            SemanticPrivacyClassifier(
                embedding_service=(
                    WrongEmbeddingService()
                ),
                model_path=self.model_path,
            )


if __name__ == "__main__":
    unittest.main()