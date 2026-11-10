import unittest

from src.privacy.context_selector import ScoredSentence
from src.privacy.minimum_disclosure import MinimumDisclosureGate


class MinimumDisclosureGateTests(unittest.TestCase):

    def setUp(self):
        self.gate = MinimumDisclosureGate()

    @staticmethod
    def item(
        text,
        score,
        index,
    ):
        return ScoredSentence(
            text=text,
            score=score,
            original_index=index,
            selection_source="rule",
        )

    def test_immediate_mode_keeps_maximum_three_sentences(self):

        items = [
            self.item(
                "Presentation is tomorrow.",
                0.75,
                0,
            ),
            self.item(
                "The deadline is Friday.",
                0.90,
                1,
            ),
            self.item(
                "Remind me Thursday to finish the report.",
                1.00,
                2,
            ),
            self.item(
                "Call the supervisor tomorrow.",
                0.85,
                3,
            ),
        ]

        result = self.gate.apply(
            items,
            mode="immediate",
        )

        self.assertEqual(
            result.disclosed_sentence_count,
            3,
        )

        self.assertEqual(
            result.selected_original_indexes,
            (1, 2, 3),
        )

        self.assertNotIn(
            "Presentation is tomorrow.",
            result.selected_sentences,
        )

    def test_pinned_trigger_is_always_kept(self):

        items = [
            self.item(
                "Important deadline is Friday.",
                1.00,
                0,
            ),
            self.item(
                "Submit the assignment tomorrow.",
                0.95,
                1,
            ),
            self.item(
                "Call the supervisor tonight.",
                0.90,
                2,
            ),
            self.item(
                "Remind me to review the report.",
                0.60,
                3,
            ),
        ]

        result = self.gate.apply(
            items,
            mode="immediate",
            pinned_original_index=3,
        )

        self.assertEqual(
            result.disclosed_sentence_count,
            3,
        )

        self.assertIn(
            3,
            result.selected_original_indexes,
        )

        self.assertIn(
            "Remind me to review the report.",
            result.selected_sentences,
        )

    def test_highest_value_supporting_sentences_are_selected(self):

        items = [
            self.item(
                "Low priority context.",
                0.50,
                0,
            ),
            self.item(
                "Useful deadline information.",
                0.90,
                1,
            ),
            self.item(
                "Reminder trigger.",
                1.00,
                2,
            ),
            self.item(
                "Another useful detail.",
                0.80,
                3,
            ),
        ]

        result = self.gate.apply(
            items,
            mode="immediate",
            pinned_original_index=2,
        )

        self.assertEqual(
            result.selected_original_indexes,
            (1, 2, 3),
        )

        self.assertNotIn(
            0,
            result.selected_original_indexes,
        )

    def test_final_output_returns_to_original_order(self):

        items = [
            self.item(
                "First useful detail.",
                0.80,
                0,
            ),
            self.item(
                "Second useful detail.",
                0.90,
                1,
            ),
            self.item(
                "Trigger sentence.",
                1.00,
                2,
            ),
        ]

        result = self.gate.apply(
            items,
            mode="immediate",
            pinned_original_index=2,
        )

        self.assertEqual(
            result.selected_original_indexes,
            (0, 1, 2),
        )

        self.assertEqual(
            result.selected_sentences,
            (
                "First useful detail.",
                "Second useful detail.",
                "Trigger sentence.",
            ),
        )

    def test_empty_input_returns_empty_result(self):

        result = self.gate.apply(
            [],
            mode="immediate",
        )

        self.assertEqual(
            result.text,
            "",
        )

        self.assertEqual(
            result.disclosed_sentence_count,
            0,
        )

        self.assertFalse(
            result.truncated,
        )

    def test_session_mode_keeps_maximum_ten_sentences(self):

        items = [
            self.item(
                f"Useful memory number {index}.",
                0.50 + (index * 0.02),
                index,
            )
            for index in range(12)
        ]

        result = self.gate.apply(
            items,
            mode="session",
        )

        self.assertEqual(
            result.disclosed_sentence_count,
            10,
        )

        self.assertEqual(
            result.excluded_sentence_count,
            2,
        )

        self.assertTrue(
            result.truncated,
        )

    def test_session_keeps_highest_value_ten_sentences(self):

        items = [
            self.item(
                f"Memory {index}.",
                score,
                index,
            )
            for index, score in enumerate(
                [
                    0.20,
                    0.30,
                    0.40,
                    0.50,
                    0.60,
                    0.70,
                    0.80,
                    0.90,
                    1.00,
                    0.95,
                    0.85,
                    0.75,
                ]
            )
        ]

        result = self.gate.apply(
            items,
            mode="session",
        )

        # The two lowest-value entries should be excluded.
        self.assertNotIn(
            0,
            result.selected_original_indexes,
        )

        self.assertNotIn(
            1,
            result.selected_original_indexes,
        )

        self.assertEqual(
            result.disclosed_sentence_count,
            10,
        )

    def test_session_respects_400_word_limit(self):

        items = [
            self.item(
                " ".join(
                    f"word{index}_{word}"
                    for word in range(100)
                ),
                1.0 - (index * 0.01),
                index,
            )
            for index in range(6)
        ]

        result = self.gate.apply(
            items,
            mode="session",
        )

        self.assertEqual(
            result.disclosed_word_count,
            400,
        )

        self.assertLessEqual(
            result.disclosed_word_count,
            400,
        )

        self.assertTrue(
            result.truncated,
        )

    def test_session_restores_original_order_after_ranking(self):

        items = [
            self.item(
                "Low value first.",
                0.20,
                0,
            ),
            self.item(
                "High value second.",
                1.00,
                1,
            ),
            self.item(
                "Medium value third.",
                0.80,
                2,
            ),
        ]

        result = self.gate.apply(
            items,
            mode="session",
        )

        self.assertEqual(
            result.selected_original_indexes,
            (0, 1, 2),
        )

        self.assertEqual(
            result.selected_sentences,
            (
                "Low value first.",
                "High value second.",
                "Medium value third.",
            ),
        )


if __name__ == "__main__":
    unittest.main()