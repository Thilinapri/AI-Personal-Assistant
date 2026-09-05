import unittest

from src.privacy.context_selector import (
    ContextSelectionResult,
    ScoredSentence,
)
from src.privacy.privacy_gateway import PrivacyGateway


class FakeContextSelector:
    """
    Lightweight test selector.

    It returns predetermined ScoredSentence objects and does
    not load MiniLM.
    """

    def __init__(self, selected_items):
        self.selected_items = selected_items

    def select(self, sentences):
        return ContextSelectionResult(
            selected_items=self.selected_items,
            original_sentence_count=len(sentences),
            semantic_scored_count=0,
        )


class PrivacyGatewayTests(unittest.TestCase):

    @staticmethod
    def item(text, score, index):
        return ScoredSentence(
            text=text,
            score=score,
            original_index=index,
            selection_source="rule",
        )

    def test_green_context_is_allowed(self):

        selector = FakeContextSelector(
            [
                self.item(
                    "Remind me tomorrow to submit the report.",
                    1.0,
                    0,
                )
            ]
        )

        gateway = PrivacyGateway(
            context_selector=selector,
        )

        result = gateway.prepare(
            sentences=[
                "Remind me tomorrow to submit the report."
            ],
            mode="immediate",
            pinned_original_index=0,
        )

        self.assertTrue(
            result.cloud_allowed
        )

        self.assertFalse(
            result.capsule.blocked
        )

        self.assertEqual(
            result.capsule.text,
            "Remind me tomorrow to submit the report.",
        )

        self.assertEqual(
            result.mapping,
            {},
        )

    def test_amber_information_is_pseudonymized(self):

        text = (
            "Remind me to email "
            "person@example.com tomorrow."
        )

        selector = FakeContextSelector(
            [
                self.item(
                    text,
                    1.0,
                    0,
                )
            ]
        )

        gateway = PrivacyGateway(
            context_selector=selector,
        )

        result = gateway.prepare(
            sentences=[text],
            mode="immediate",
            pinned_original_index=0,
        )

        self.assertTrue(
            result.cloud_allowed
        )

        self.assertFalse(
            result.capsule.blocked
        )

        self.assertEqual(
            result.capsule.text,
            (
                "Remind me to email "
                "<EMAIL_1> tomorrow."
            ),
        )

        self.assertNotIn(
            "person@example.com",
            result.capsule.text,
        )

        self.assertEqual(
            result.mapping["<EMAIL_1>"],
            "person@example.com",
        )

        self.assertIn(
            "EMAIL",
            result.capsule.redacted_types,
        )

    def test_pure_red_secret_fails_closed(self):

        text = "My password is Secret123."

        selector = FakeContextSelector(
            [
                self.item(
                    text,
                    1.0,
                    0,
                )
            ]
        )

        gateway = PrivacyGateway(
            context_selector=selector,
        )

        result = gateway.prepare(
            sentences=[text],
            mode="immediate",
            pinned_original_index=0,
        )

        self.assertFalse(
            result.cloud_allowed
        )

        self.assertTrue(
            result.capsule.blocked
        )

        self.assertEqual(
            result.capsule.text,
            "",
        )

        self.assertEqual(
            result.capsule.block_reason,
            "red_secret_only",
        )

        self.assertIn(
            "PASSWORD",
            result.capsule.redacted_types,
        )

        self.assertEqual(
            result.mapping,
            {},
        )

    def test_mixed_red_sentence_preserves_safe_intent(self):

        text = (
            "My password is Secret123 "
            "and remind me tomorrow to change it."
        )

        selector = FakeContextSelector(
            [
                self.item(
                    text,
                    1.0,
                    0,
                ),
            ]
        )

        gateway = PrivacyGateway(
            context_selector=selector,
        )

        result = gateway.prepare(
            sentences=[text],
            mode="immediate",
            pinned_original_index=0,
        )

        self.assertTrue(
            result.cloud_allowed
        )

        self.assertFalse(
            result.capsule.blocked
        )

        self.assertNotIn(
            "Secret123",
            result.capsule.text,
        )

        self.assertIn(
            "<REDACTED_PASSWORD>",
            result.capsule.text,
        )

        self.assertIn(
            "remind me tomorrow to change it",
            result.capsule.text.lower(),
        )

        self.assertIn(
            "PASSWORD",
            result.capsule.redacted_types,
        )

        # RED values are never locally mapped for restoration.
        self.assertEqual(
            result.mapping,
            {},
        )

    def test_red_only_sentence_is_dropped_but_safe_context_survives(self):

        secret = "My password is Secret123."

        reminder = (
            "Remind me tomorrow to change my password."
        )

        selector = FakeContextSelector(
            [
                self.item(
                    secret,
                    0.80,
                    0,
                ),
                self.item(
                    reminder,
                    1.00,
                    1,
                ),
            ]
        )

        gateway = PrivacyGateway(
            context_selector=selector,
        )

        result = gateway.prepare(
            sentences=[
                secret,
                reminder,
            ],
            mode="immediate",
            pinned_original_index=1,
        )

        self.assertTrue(
            result.cloud_allowed
        )

        self.assertNotIn(
            "Secret123",
            result.capsule.text,
        )

        self.assertNotIn(
            "<REDACTED_PASSWORD>",
            result.capsule.text,
        )

        self.assertEqual(
            result.capsule.text,
            reminder,
        )

        self.assertIn(
            "PASSWORD",
            result.capsule.redacted_types,
        )

    def test_api_key_is_redacted_from_safe_reminder(self):

        text = (
            "Remind me Friday to rotate "
            "API key ABCDEFGHIJK."
        )

        selector = FakeContextSelector(
            [
                self.item(
                    text,
                    1.0,
                    0,
                )
            ]
        )

        gateway = PrivacyGateway(
            context_selector=selector,
        )

        result = gateway.prepare(
            sentences=[text],
            mode="immediate",
            pinned_original_index=0,
        )

        self.assertTrue(
            result.cloud_allowed
        )

        self.assertEqual(
            result.capsule.text,
            (
                "Remind me Friday to rotate "
                "<REDACTED_API_KEY>."
            ),
        )

        self.assertEqual(
            result.mapping,
            {},
        )

        self.assertIn(
            "API_KEY",
            result.capsule.redacted_types,
        )

    def test_immediate_mode_applies_minimum_disclosure(self):

        selector = FakeContextSelector(
            [
                self.item(
                    "Presentation is tomorrow.",
                    0.75,
                    0,
                ),
                self.item(
                    "Deadline is Friday.",
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
        )

        gateway = PrivacyGateway(
            context_selector=selector,
        )

        result = gateway.prepare(
            sentences=[
                "Presentation is tomorrow.",
                "Deadline is Friday.",
                "Remind me Thursday to finish the report.",
                "Call the supervisor tomorrow.",
            ],
            mode="immediate",
            pinned_original_index=2,
        )

        self.assertTrue(
            result.cloud_allowed
        )

        self.assertEqual(
            result.capsule.selected_sentence_count,
            3,
        )

        self.assertIn(
            "Remind me Thursday to finish the report.",
            result.capsule.text,
        )

        self.assertNotIn(
            "Presentation is tomorrow.",
            result.capsule.text,
        )

    def test_no_relevant_context_is_blocked_locally(self):

        selector = FakeContextSelector(
            []
        )

        gateway = PrivacyGateway(
            context_selector=selector,
        )

        result = gateway.prepare(
            sentences=[
                "Hello.",
                "Okay.",
            ],
            mode="session",
        )

        self.assertFalse(
            result.cloud_allowed
        )

        self.assertTrue(
            result.capsule.blocked
        )

        self.assertEqual(
            result.capsule.text,
            "",
        )

        self.assertEqual(
            result.capsule.block_reason,
            "no_relevant_context",
        )

    def test_amber_output_can_be_rehydrated_locally(self):

        text = (
            "Remind me to email "
            "person@example.com tomorrow."
        )

        selector = FakeContextSelector(
            [
                self.item(
                    text,
                    1.0,
                    0,
                )
            ]
        )

        gateway = PrivacyGateway(
            context_selector=selector,
        )

        result = gateway.prepare(
            sentences=[text],
            mode="immediate",
            pinned_original_index=0,
        )

        restored = gateway.rehydrate_output(
            result.capsule.text,
            result.mapping,
        )

        self.assertEqual(
            restored,
            text,
        )


if __name__ == "__main__":
    unittest.main()