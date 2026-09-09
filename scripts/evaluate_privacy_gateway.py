import csv
import json
import time
from pathlib import Path

from src.memory.embedding_service import EmbeddingService
from src.privacy.context_selector import ContextSelector
from src.privacy.minimum_disclosure import (
    MinimumDisclosureGate,
)
from src.privacy.privacy_gateway import PrivacyGateway
from src.privacy.semantic_privacy_classifier import (
    SemanticPrivacyClassifier,
)


DATA_PATH = Path(
    "data/privacy/gateway_evaluation.jsonl"
)

RESULTS_PATH = Path(
    "results/privacy_gateway_evaluation.csv"
)

BASELINE_RESULTS_PATH = Path(
    "results/privacy_gateway_baseline.csv"
)

DETERMINISTIC_RESULTS_PATH = Path(
    "results/privacy_gateway_deterministic.csv"
)

HYBRID_RESULTS_PATH = Path(
    "results/privacy_gateway_hybrid.csv"
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


def word_count(text):
    return len(
        text.split()
    )


def contains_value(
    text,
    value,
):
    return (
        value.lower()
        in text.lower()
    )


class BaselineResult:
    """
    Minimal result object used by the evaluation baseline.

    The baseline applies context relevance and minimum
    disclosure, but intentionally performs no sensitive-data
    protection.
    """

    def __init__(
        self,
        text,
        original_sentence_count,
        selected_sentence_count,
    ):
        self.cloud_allowed = bool(
            text.strip()
        )

        self.capsule = type(
            "BaselineCapsule",
            (),
            {
                "text": text,
                "risk_level": "none",
                "block_reason": None,
                "redacted_types": [],
                "original_sentence_count": (
                    original_sentence_count
                ),
                "selected_sentence_count": (
                    selected_sentence_count
                ),
            },
        )()


class BaselineGateway:
    """
    Evaluation-only baseline.

    Uses the same ContextSelector and MinimumDisclosureGate,
    but deliberately skips privacy detection, pseudonymization,
    and semantic privacy screening.
    """

    def __init__(
        self,
        context_selector,
        disclosure_gate=None,
    ):
        self.context_selector = (
            context_selector
        )

        self.disclosure_gate = (
            disclosure_gate
            if disclosure_gate is not None
            else MinimumDisclosureGate()
        )

    def prepare(
        self,
        sentences,
        mode,
        purpose="privacy_evaluation",
        pinned_original_index=None,
    ):
        selection = (
            self.context_selector.select(
                sentences
            )
        )

        if not selection.selected_items:
            return BaselineResult(
                text="",
                original_sentence_count=(
                    selection.original_sentence_count
                ),
                selected_sentence_count=0,
            )

        disclosure = (
            self.disclosure_gate.apply(
                selection.selected_items,
                mode=mode,
                pinned_original_index=(
                    pinned_original_index
                ),
            )
        )

        return BaselineResult(
            text=disclosure.text,
            original_sentence_count=(
                selection.original_sentence_count
            ),
            selected_sentence_count=(
                disclosure.disclosed_sentence_count
            ),
        )


def evaluate_configuration(
    rows,
    gateway,
    label,
    results_path,
):
    """
    Evaluate one privacy configuration using the same
    scenarios and metrics.

    Keeping this logic shared ensures that BASELINE,
    DETERMINISTIC, and HYBRID are compared fairly.
    """

    results_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = []

    total_original_words = 0
    total_disclosed_words = 0

    total_sensitive_values = 0
    total_leaked_values = 0

    total_utility_terms = 0
    total_retained_utility_terms = 0

    correct_cloud_decisions = 0

    latencies = []

    print()
    print(
        "Running Privacy Gateway evaluation..."
    )
    print()

    for row in rows:

        sentences = row["sentences"]
        mode = row["mode"]

        expected_cloud_allowed = row[
            "expected_cloud_allowed"
        ]

        pinned_original_index = (
            len(sentences) - 1
            if (
                mode == "immediate"
                and sentences
            )
            else None
        )

        start_time = (
            time.perf_counter()
        )

        result = gateway.prepare(
            sentences=sentences,
            mode=mode,
            purpose="privacy_evaluation",
            pinned_original_index=(
                pinned_original_index
            ),
        )

        latency_ms = (
            (
                time.perf_counter()
                - start_time
            )
            * 1000.0
        )

        latencies.append(
            latency_ms
        )

        outbound_text = (
            result.capsule.text
            if result.cloud_allowed
            else ""
        )

        original_text = " ".join(
            sentences
        )

        original_words = (
            word_count(
                original_text
            )
        )

        disclosed_words = (
            word_count(
                outbound_text
            )
        )

        cdr = (
            disclosed_words
            / original_words
            if original_words
            else 0.0
        )

        sensitive_values = row.get(
            "sensitive_values",
            [],
        )

        leaked_values = [
            value
            for value
            in sensitive_values
            if contains_value(
                outbound_text,
                value,
            )
        ]

        sensitive_count = len(
            sensitive_values
        )

        leak_count = len(
            leaked_values
        )

        selr = (
            leak_count
            / sensitive_count
            if sensitive_count
            else 0.0
        )

        utility_terms = row.get(
            "utility_terms",
            [],
        )

        retained_utility_terms = [
            term
            for term
            in utility_terms
            if contains_value(
                outbound_text,
                term,
            )
        ]

        utility_count = len(
            utility_terms
        )

        retained_utility_count = len(
            retained_utility_terms
        )

        utility_retention = (
            retained_utility_count
            / utility_count
            if utility_count
            else 0.0
        )

        decision_correct = (
            result.cloud_allowed
            == expected_cloud_allowed
        )

        if decision_correct:
            correct_cloud_decisions += 1

        total_original_words += (
            original_words
        )

        total_disclosed_words += (
            disclosed_words
        )

        total_sensitive_values += (
            sensitive_count
        )

        total_leaked_values += (
            leak_count
        )

        total_utility_terms += (
            utility_count
        )

        total_retained_utility_terms += (
            retained_utility_count
        )

        evaluation_row = {
            "configuration": label,
            "id": row["id"],
            "category": row["category"],
            "mode": mode,
            "expected_cloud_allowed": (
                expected_cloud_allowed
            ),
            "actual_cloud_allowed": (
                result.cloud_allowed
            ),
            "decision_correct": (
                decision_correct
            ),
            "original_words": (
                original_words
            ),
            "disclosed_words": (
                disclosed_words
            ),
            "cdr": round(
                cdr,
                4,
            ),
            "sensitive_value_count": (
                sensitive_count
            ),
            "leaked_sensitive_count": (
                leak_count
            ),
            "selr": round(
                selr,
                4,
            ),
            "utility_term_count": (
                utility_count
            ),
            "retained_utility_count": (
                retained_utility_count
            ),
            "utility_retention": round(
                utility_retention,
                4,
            ),
            "latency_ms": round(
                latency_ms,
                3,
            ),
            "risk_level": (
                result.capsule.risk_level
            ),
            "blocked_reason": (
                result.capsule.block_reason
                or ""
            ),
            "redacted_types": (
                ",".join(
                    result.capsule.redacted_types
                )
            ),
        }

        results.append(
            evaluation_row
        )

        print(
            row["id"],
            row["category"],
            "| allowed=",
            result.cloud_allowed,
            "| CDR=",
            f"{cdr:.3f}",
            "| leaks=",
            leak_count,
            "| utility=",
            f"{utility_retention:.3f}",
            "| latency=",
            f"{latency_ms:.2f} ms",
        )

    fieldnames = list(
        results[0].keys()
    )

    with results_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            results
        )

    overall_cdr = (
        total_disclosed_words
        / total_original_words
        if total_original_words
        else 0.0
    )

    overall_selr = (
        total_leaked_values
        / total_sensitive_values
        if total_sensitive_values
        else 0.0
    )

    overall_utility = (
        total_retained_utility_terms
        / total_utility_terms
        if total_utility_terms
        else 0.0
    )

    decision_accuracy = (
        correct_cloud_decisions
        / len(rows)
        if rows
        else 0.0
    )

    average_latency = (
        sum(latencies)
        / len(latencies)
        if latencies
        else 0.0
    )

    maximum_latency = (
        max(latencies)
        if latencies
        else 0.0
    )

    print()
    print(
        "========================================"
    )
    print(
        f"Privacy Gateway Evaluation Summary - {label}"
    )
    print(
        "========================================"
    )

    print(
        f"Scenarios: {len(rows)}"
    )

    print(
        "Cloud decision accuracy:",
        f"{decision_accuracy:.3f}",
    )

    print(
        "Context Disclosure Ratio (CDR):",
        f"{overall_cdr:.3f}",
    )

    print(
        "Sensitive Exposure Leakage Rate (SELR):",
        f"{overall_selr:.3f}",
    )

    print(
        "Memory Utility Retention:",
        f"{overall_utility:.3f}",
    )

    print(
        "Average privacy latency:",
        f"{average_latency:.2f} ms",
    )

    print(
        "Maximum privacy latency:",
        f"{maximum_latency:.2f} ms",
    )

    print(
        "Sensitive values tested:",
        total_sensitive_values,
    )

    print(
        "Sensitive values leaked:",
        total_leaked_values,
    )

    print()
    print(
        "Results written to:",
        results_path,
    )

    return {
        "label": label,
        "scenarios": len(rows),
        "decision_accuracy": (
            decision_accuracy
        ),
        "cdr": overall_cdr,
        "selr": overall_selr,
        "utility_retention": (
            overall_utility
        ),
        "average_latency_ms": (
            average_latency
        ),
        "maximum_latency_ms": (
            maximum_latency
        ),
        "sensitive_values_tested": (
            total_sensitive_values
        ),
        "sensitive_values_leaked": (
            total_leaked_values
        ),
    }


def main():

    rows = load_jsonl(
        DATA_PATH
    )

    print(
        f"Loaded {len(rows)} gateway scenarios."
    )

    print(
        "Loading shared MiniLM..."
    )

    embedding_service = (
        EmbeddingService()
    )

    context_selector = (
        ContextSelector(
            embedding_service=(
                embedding_service
            )
        )
    )

    semantic_classifier = (
        SemanticPrivacyClassifier(
            embedding_service=(
                embedding_service
            )
        )
    )

    baseline_gateway = BaselineGateway(
        context_selector=context_selector
    )

    # Deterministic privacy configuration:
    # context relevance + RED/AMBER protection
    # without semantic privacy classification.
    deterministic_gateway = PrivacyGateway(
        context_selector=context_selector,
        semantic_classifier=None,
    )

    # Hybrid privacy configuration:
    # deterministic protection + semantic privacy.
    #
    # Both configurations reuse the same ContextSelector
    # and the same shared MiniLM embedding service.
    hybrid_gateway = PrivacyGateway(
        context_selector=context_selector,
        semantic_classifier=(
            semantic_classifier
        ),
    )

    # Warm up the shared embedding model before
    # latency measurements.
    embedding_service.encode(
        "Privacy evaluation warm up."
    )

    baseline_summary = evaluate_configuration(
        rows=rows,
        gateway=baseline_gateway,
        label="BASELINE",
        results_path=BASELINE_RESULTS_PATH,
    )

    deterministic_summary = evaluate_configuration(
        rows=rows,
        gateway=deterministic_gateway,
        label="DETERMINISTIC",
        results_path=DETERMINISTIC_RESULTS_PATH,
    )

    hybrid_summary = evaluate_configuration(
        rows=rows,
        gateway=hybrid_gateway,
        label="HYBRID",
        results_path=HYBRID_RESULTS_PATH,
    )

    summaries = [
        baseline_summary,
        deterministic_summary,
        hybrid_summary,
    ]

    print()
    print(
        "==============================================="
    )
    print(
        "Privacy Configuration Comparison"
    )
    print(
        "==============================================="
    )

    print(
        f"{'Configuration':<15}"
        f"{'Accuracy':>10}"
        f"{'CDR':>10}"
        f"{'SELR':>10}"
        f"{'Utility':>10}"
        f"{'Avg ms':>10}"
    )

    for summary in summaries:
        print(
            f"{summary['label']:<15}"
            f"{summary['decision_accuracy']:>10.3f}"
            f"{summary['cdr']:>10.3f}"
            f"{summary['selr']:>10.3f}"
            f"{summary['utility_retention']:>10.3f}"
            f"{summary['average_latency_ms']:>10.2f}"
        )


if __name__ == "__main__":
    main()