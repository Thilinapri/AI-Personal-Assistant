import unittest

from src.privacy.context_selector import ContextSelector


class FakeEmbeddingService:
    """
    Small deterministic stand-in for MiniLM.

    Memory prototypes are represented by [1.0, 0.0].

    Relevant uncertain sentences receive a vector close to
    the prototypes, while irrelevant sentences receive an
    unrelated vector.
    """

    def __init__(self):
        self.calls = []

    def encode_many(self, texts):
        texts = list(texts)
        self.calls.append(texts)

        # ContextSelector embeds its memory prototypes once
        # during initialization.
        if (
            texts
            and texts[0].startswith(
                "Remember an appointment"
            )
        ):
            return [
                [1.0, 0.0]
                for _ in texts
            ]

        embeddings = []

        for text in texts:
            lowered = text.lower()

            if "dentist moved the slot" in lowered:
                embeddings.append(
                    [0.80, 0.20]
                )
            else:
                embeddings.append(
                    [0.0, 1.0]
                )

        return embeddings


class ContextSelectorTests(unittest.TestCase):

    def setUp(self):
        self.embedding_service = FakeEmbeddingService()

        self.selector = ContextSelector(
            embedding_service=self.embedding_service,
            semantic_threshold=0.45,
        )

        # Ignore the prototype embedding call when
        # checking later selection-time calls.
        self.embedding_service.calls.clear()

    def test_strong_reminder_signal_is_kept(self):

        result = self.selector.select(
            [
                "Remind me tomorrow to submit the report.",
            ]
        )

        self.assertEqual(
            result.selected_sentences,
            [
                "Remind me tomorrow to submit the report.",
            ],
        )

        self.assertEqual(
            result.semantic_scored_count,
            0,
        )

        self.assertEqual(
            self.embedding_service.calls,
            [],
        )

    def test_filler_is_dropped_without_semantic_scoring(self):

        result = self.selector.select(
            [
                "Okay.",
                "Thank you.",
            ]
        )

        self.assertEqual(
            result.selected_sentences,
            [],
        )

        self.assertEqual(
            result.semantic_scored_count,
            0,
        )

        self.assertEqual(
            self.embedding_service.calls,
            [],
        )

    def test_uncertain_relevant_sentence_is_kept_semantically(self):

        result = self.selector.select(
            [
                "The dentist moved the slot again.",
            ]
        )

        self.assertEqual(
            result.selected_sentences,
            [
                "The dentist moved the slot again.",
            ],
        )

        self.assertEqual(
            result.semantic_scored_count,
            1,
        )

    def test_uncertain_irrelevant_sentence_is_dropped(self):

        result = self.selector.select(
            [
                "The wall is painted blue.",
            ]
        )

        self.assertEqual(
            result.selected_sentences,
            [],
        )

        self.assertEqual(
            result.semantic_scored_count,
            1,
        )

    def test_uncertain_sentences_are_batched(self):

        result = self.selector.select(
            [
                "The dentist moved the slot again.",
                "The wall is painted blue.",
            ]
        )

        self.assertEqual(
            result.selected_sentences,
            [
                "The dentist moved the slot again.",
            ],
        )

        self.assertEqual(
            result.semantic_scored_count,
            2,
        )

        self.assertEqual(
            len(self.embedding_service.calls),
            1,
        )

        self.assertEqual(
            len(self.embedding_service.calls[0]),
            2,
        )

    def test_original_order_is_preserved(self):

        result = self.selector.select(
            [
                "The dentist moved the slot again.",
                "Okay.",
                "Remind me Friday to send the report.",
            ]
        )

        self.assertEqual(
            result.selected_sentences,
            [
                "The dentist moved the slot again.",
                "Remind me Friday to send the report.",
            ],
        )

    def test_temporal_signal_is_kept_without_semantic_scoring(self):

        result = self.selector.select(
            [
                "The presentation is tomorrow.",
            ]
        )

        self.assertEqual(
            result.selected_sentences,
            [
                "The presentation is tomorrow.",
            ],
        )

        self.assertEqual(
            result.semantic_scored_count,
            0,
        )

    def test_empty_input_returns_empty_result(self):

        result = self.selector.select([])

        self.assertEqual(
            result.selected_sentences,
            [],
        )

        self.assertEqual(
            result.original_sentence_count,
            0,
        )

        self.assertEqual(
            result.semantic_scored_count,
            0,
        )

    def test_invalid_threshold_is_rejected(self):

        with self.assertRaises(ValueError):
            ContextSelector(
                embedding_service=FakeEmbeddingService(),
                semantic_threshold=1.5,
            )

    def test_explicit_reminder_gets_highest_rule_score(self):

        result = self.selector.select(
            [
                "Remind me Friday to submit the report.",
            ]
        )

        item = result.selected_items[0]

        self.assertEqual(
            item.score,
            1.0,
        )

        self.assertEqual(
            item.selection_source,
            "rule",
        )

    def test_deadline_outranks_date_only_sentence(self):

        result = self.selector.select(
            [
                "The deadline is next week.",
                "The presentation is tomorrow.",
            ]
        )

        deadline = result.selected_items[0]
        temporal = result.selected_items[1]

        self.assertEqual(
            deadline.score,
            0.90,
        )

        self.assertEqual(
            temporal.score,
            0.75,
        )

        self.assertGreater(
            deadline.score,
            temporal.score,
        )

    def test_semantic_selection_keeps_similarity_score(self):

        result = self.selector.select(
            [
                "The dentist moved the slot again.",
            ]
        )

        item = result.selected_items[0]

        self.assertAlmostEqual(
            item.score,
            0.80,
        )

        self.assertEqual(
            item.selection_source,
            "semantic",
        )

    def test_selected_item_keeps_original_index(self):

        result = self.selector.select(
            [
                "Okay.",
                "The wall is painted blue.",
                "Remind me Friday to send the report.",
            ]
        )

        item = result.selected_items[0]

        self.assertEqual(
            item.text,
            "Remind me Friday to send the report.",
        )

        self.assertEqual(
            item.original_index,
            2,
        )


if __name__ == "__main__":
    unittest.main()