import json
import math
from pathlib import Path

import numpy as np

from src.memory.embedding_service import EmbeddingService


MODEL_PATH = Path(
    "src/privacy/models/semantic_privacy_classifier.json"
)

TEST_PATH = Path(
    "data/privacy/test.jsonl"
)


def load_jsonl(path):
    rows = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            line = line.strip()

            if line:
                rows.append(
                    json.loads(line)
                )

    return rows


def sigmoid(value):

    if value >= 0:
        return 1.0 / (
            1.0 + math.exp(-value)
        )

    exp_value = math.exp(value)

    return exp_value / (
        1.0 + exp_value
    )


def main():

    with MODEL_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        model = json.load(file)

    weights = np.asarray(
        model["weights"],
        dtype=np.float32,
    )

    bias = float(
        model["bias"]
    )

    safe_threshold = float(
        model["safe_threshold"]
    )

    sensitive_threshold = float(
        model["sensitive_threshold"]
    )

    test_rows = load_jsonl(
        TEST_PATH
    )

    texts = [
        row["text"]
        for row in test_rows
    ]

    labels = [
        row["label"]
        for row in test_rows
    ]

    print(
        "Safe threshold:",
        safe_threshold,
    )

    print(
        "Sensitive threshold:",
        sensitive_threshold,
    )

    print(
        "Loading shared MiniLM..."
    )

    embedding_service = (
        EmbeddingService()
    )

    embeddings = np.asarray(
        embedding_service.encode_many(
            texts
        ),
        dtype=np.float32,
    )

    tp = 0
    fp = 0
    tn = 0
    fn = 0

    zone_counts = {
        "SAFE": 0,
        "UNCERTAIN": 0,
        "SENSITIVE": 0,
    }

    print()
    print("Held-out test results:")

    for row, embedding, actual in zip(
        test_rows,
        embeddings,
        labels,
    ):

        logit = (
            float(
                np.dot(
                    weights,
                    embedding,
                )
            )
            + bias
        )

        probability = sigmoid(
            logit
        )

        if probability < safe_threshold:
            zone = "SAFE"

        elif probability < sensitive_threshold:
            zone = "UNCERTAIN"

        else:
            zone = "SENSITIVE"

        zone_counts[zone] += 1

        # Privacy-oriented binary decision:
        # UNCERTAIN is NOT considered cloud-safe.
        predicted_sensitive = (
            probability >= safe_threshold
        )

        if actual == 1:

            if predicted_sensitive:
                tp += 1
            else:
                fn += 1

        else:

            if predicted_sensitive:
                fp += 1
            else:
                tn += 1

        print(
            f"{probability:.4f}",
            zone,
            "actual=",
            actual,
            "|",
            row["text"],
        )

    precision = (
        tp / (tp + fp)
        if (tp + fp)
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn)
        else 0.0
    )

    accuracy = (
        (tp + tn)
        / len(test_rows)
    )

    print()
    print("Final held-out metrics:")
    print("TP:", tp)
    print("FP:", fp)
    print("TN:", tn)
    print("FN:", fn)

    print(
        f"Accuracy: {accuracy:.3f}"
    )

    print(
        f"Precision: {precision:.3f}"
    )

    print(
        f"Sensitive recall: {recall:.3f}"
    )

    print(
        "Zone counts:",
        zone_counts,
    )


if __name__ == "__main__":
    main()
    