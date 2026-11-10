import unittest

from src.privacy.context_selector import (
    ContextSelectionResult,
    ScoredSentence,
)
from src.privacy.privacy_gateway import (
    PrivacyGateway,
)


class PassthroughContextSelector:
    """
    Select every supplied sentence.

    This keeps the test focused on the privacy boundary
    without loading MiniLM.
    """

    def select(
        self,
        sentences,
    ):
        selected_items = [
            ScoredSentence(
                text=sentence,
                score=1.0,
                original_index=index,
                selection_source="test",
            )
            for index, sentence
            in enumerate(sentences)
        ]

        return ContextSelectionResult(
            selected_items=selected_items,
            original_sentence_count=len(sentences),
            semantic_scored_count=0,
        )


class PrivacyOutboundLeakageTests(
    unittest.TestCase
):

    def setUp(self):

        self.gateway = PrivacyGateway(
            context_selector=(
                PassthroughContextSelector()
            )
        )

    def test_red_secrets_never_appear_in_outbound_capsule(
        self,
    ):

        samples = [
            {
                "name": "password",
                "text": (
                    "Remind me tomorrow to change "
                    "my password is DemoPass123!"
                ),
                "secret": "DemoPass123!",
            },
            {
                "name": "pin",
                "text": (
                    "Remind me tomorrow to change "
                    "my PIN code is 4826"
                ),
                "secret": "4826",
            },
            {
                "name": "api_key",
                "text": (
                    "Remind me tomorrow to rotate "
                    "my API key is "
                    "DEMO_API_KEY_1234567890"
                ),
                "secret": (
                    "DEMO_API_KEY_1234567890"
                ),
            },
            {
                "name": "payment_card",
                "text": (
                    "Remind me tomorrow to update "
                    "the card linked to "
                    "4111 1111 1111 1111"
                ),
                "secret": (
                    "4111 1111 1111 1111"
                ),
            },
            {
                "name": "card_security_code",
                "text": (
                    "Remind me tomorrow to update "
                    "the card with CVV 123"
                ),
                "secret": "123",
            },
        ]

        for sample in samples:

            with self.subTest(
                sample=sample["name"]
            ):

                result = self.gateway.prepare(
                    sentences=[
                        sample["text"]
                    ],
                    mode="immediate",
                    pinned_original_index=0,
                )

                self.assertNotIn(
                    sample["secret"],
                    result.capsule.text,
                )

                self.assertNotIn(
                    sample["secret"],
                    result.mapping.values(),
                )

    def test_amber_values_are_not_exposed_in_outbound_capsule(
        self,
    ):

        samples = [
            {
                "name": "email",
                "text": (
                    "Remind me tomorrow to email "
                    "demo.user@example.com"
                ),
                "private_value": (
                    "demo.user@example.com"
                ),
            },
            {
                "name": "phone",
                "text": (
                    "Remind me tomorrow to call "
                    "0771234567"
                ),
                "private_value": "0771234567",
            },
            {
                "name": "nic",
                "text": (
                    "Remind me tomorrow to bring "
                    "my NIC 200012345678"
                ),
                "private_value": (
                    "200012345678"
                ),
            },
            {
                "name": "passport",
                "text": (
                    "Remind me tomorrow to bring "
                    "my passport number N1234567"
                ),
                "private_value": (
                    "N1234567"
                ),
            },
            {
                "name": "date_of_birth",
                "text": (
                    "Remind me tomorrow to update "
                    "my date of birth 15/08/2002"
                ),
                "private_value": (
                    "15/08/2002"
                ),
            },
            {
                "name": "address",
                "text": (
                    "Remind me tomorrow to update "
                    "my home address at "
                    "25 Example Road, Colombo."
                ),
                "private_value": (
                    "25 Example Road, Colombo"
                ),
            },
        ]

        for sample in samples:

            with self.subTest(
                sample=sample["name"]
            ):

                result = self.gateway.prepare(
                    sentences=[
                        sample["text"]
                    ],
                    mode="immediate",
                    pinned_original_index=0,
                )

                self.assertTrue(
                    result.cloud_allowed,
                    msg=sample["name"],
                )

                self.assertNotIn(
                    sample["private_value"],
                    result.capsule.text,
                    msg=sample["name"],
                )

                self.assertTrue(
                    result.mapping,
                    msg=sample["name"],
                )


if __name__ == "__main__":
    unittest.main()