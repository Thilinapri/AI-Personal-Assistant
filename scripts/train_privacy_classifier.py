import json
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)

from src.memory.embedding_service import EmbeddingService


TRAIN_PATH = Path("data/privacy/train.jsonl")
VALIDATION_PATH = Path("data/privacy/validation.jsonl")
MODEL_OUTPUT_PATH = Path(
    "src/privacy/models/semantic_privacy_classifier.json"
)


def load_jsonl(path):
    rows = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            rows.append(json.loads(line))

    return rows


def main():

    train_rows = load_jsonl(TRAIN_PATH)
    validation_rows = load_jsonl(VALIDATION_PATH)

    train_texts = [
        row["text"]
        for row in train_rows
    ]

    train_labels = np.array(
        [
            row["label"]
            for row in train_rows
        ],
        dtype=np.int64,
    )

    validation_texts = [
        row["text"]
        for row in validation_rows
    ]

    validation_labels = np.array(
        [
            row["label"]
            for row in validation_rows
        ],
        dtype=np.int64,
    )

    print("Loading shared MiniLM embedding model...")

    embedding_service = EmbeddingService()

    print("Encoding training examples...")

    train_embeddings = np.asarray(
        embedding_service.encode_many(
            train_texts
        ),
        dtype=np.float32,
    )

    print("Encoding validation examples...")

    validation_embeddings = np.asarray(
        embedding_service.encode_many(
            validation_texts
        ),
        dtype=np.float32,
    )

    print(
        "Training embedding shape:",
        train_embeddings.shape,
    )

    print(
        "Validation embedding shape:",
        validation_embeddings.shape,
    )

    classifier = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=42,
    )

    classifier.fit(
        train_embeddings,
        train_labels,
    )

    MODEL_OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    model_data = {
        "embedding_model": (
            EmbeddingService.DEFAULT_MODEL
        ),
        "embedding_dimension": int(
            train_embeddings.shape[1]
        ),
        "weights": (
            classifier.coef_[0]
            .astype(float)
            .tolist()
        ),
        "bias": float(
            classifier.intercept_[0]
        ),
        "safe_threshold": 0.45,
        "sensitive_threshold": 0.55,
    }

    with MODEL_OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            model_data,
            file,
            indent=2,
        )

    print()
    print(
        "Exported classifier to:",
        MODEL_OUTPUT_PATH,
    )

    print(
        "Exported weights:",
        len(model_data["weights"]),
    )

    predictions = classifier.predict(
        validation_embeddings
    )

    probabilities = classifier.predict_proba(
        validation_embeddings
    )[:, 1]

    print()
    print("Validation accuracy:")
    print(
        accuracy_score(
            validation_labels,
            predictions,
        )
    )

    print()
    print("Confusion matrix:")
    print(
        confusion_matrix(
            validation_labels,
            predictions,
        )
    )

    print()
    print("Classification report:")
    print(
        classification_report(
            validation_labels,
            predictions,
            digits=3,
        )
    )

    print()
    print("Validation predictions:")

    for row, probability, prediction in zip(
        validation_rows,
        probabilities,
        predictions,
    ):

        print(
            f"{probability:.4f}",
            "pred=",
            int(prediction),
            "actual=",
            row["label"],
            "|",
            row["text"],
        )

    print()
    print("Threshold analysis:")

    for threshold in [
        0.40,
        0.45,
        0.50,
        0.55,
        0.60,
    ]:

        threshold_predictions = (
            probabilities >= threshold
        ).astype(int)

        matrix = confusion_matrix(
            validation_labels,
            threshold_predictions,
        )

        tn, fp, fn, tp = matrix.ravel()

        recall = (
            tp / (tp + fn)
            if (tp + fn)
            else 0.0
        )

        precision = (
            tp / (tp + fp)
            if (tp + fp)
            else 0.0
        )

        print(
            f"threshold={threshold:.2f} "
            f"TP={tp} FP={fp} "
            f"TN={tn} FN={fn} "
            f"precision={precision:.3f} "
            f"recall={recall:.3f}"
        )

    safe_threshold = 0.45
    sensitive_threshold = 0.55

    safe_count = 0
    uncertain_count = 0
    sensitive_count = 0

    print()
    print("Three-zone validation decisions:")

    for row, probability in zip(
        validation_rows,
        probabilities,
    ):

        if probability < safe_threshold:
            decision = "SAFE"
            safe_count += 1

        elif probability >= sensitive_threshold:
            decision = "SENSITIVE"
            sensitive_count += 1

        else:
            decision = "UNCERTAIN"
            uncertain_count += 1

        print(
            f"{probability:.4f}",
            decision,
            "actual=",
            row["label"],
            "|",
            row["text"],
        )

    print()
    print(
        "Zone counts:",
        {
            "safe": safe_count,
            "uncertain": uncertain_count,
            "sensitive": sensitive_count,
        },
    )


if __name__ == "__main__":
    main()