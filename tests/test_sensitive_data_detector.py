import unittest

from src.privacy import SensitiveDataDetector


class SensitiveDataDetectorTests(unittest.TestCase):

    def setUp(self):
        self.detector = SensitiveDataDetector()

    def test_detects_password(self):

        text = "My password is DemoPass123!"

        entities = self.detector.detect(text)

        self.assertEqual(len(entities), 1)
        self.assertEqual(
            entities[0].entity_type,
            "PASSWORD",
        )
        self.assertEqual(
            entities[0].risk,
            "red",
        )

    def test_detects_pin(self):

        text = "My PIN code is 4826"

        entities = self.detector.detect(text)

        self.assertEqual(len(entities), 1)
        self.assertEqual(
            entities[0].entity_type,
            "PIN",
        )

    def test_detects_api_key(self):

        text = (
            "My API key is "
            "DEMO_API_KEY_1234567890"
        )

        entities = self.detector.detect(text)

        self.assertEqual(len(entities), 1)
        self.assertEqual(
            entities[0].entity_type,
            "API_KEY",
        )

    def test_detects_bearer_token(self):

        text = (
            "Authorization uses Bearer "
            "demo.token.value12345"
        )

        entities = self.detector.detect(text)

        self.assertEqual(len(entities), 1)
        self.assertEqual(
            entities[0].entity_type,
            "BEARER_TOKEN",
        )

    def test_normal_text_is_not_flagged(self):

        text = (
            "The password policy requires "
            "strong passwords."
        )

        entities = self.detector.detect(text)

        self.assertEqual(entities, [])
        self.assertFalse(
            self.detector.has_red_secret(text)
        )

    def test_detects_email_as_amber(self):

        text = "Email me at demo.user@example.com"

        entities = self.detector.detect(text)

        self.assertEqual(len(entities), 1)
        self.assertEqual(
            entities[0].entity_type,
            "EMAIL",
        )
        self.assertEqual(
            entities[0].risk,
            "amber",
        )

    def test_detects_local_sri_lankan_phone(self):

        text = "My phone number is 0771234567"

        entities = self.detector.detect(text)

        self.assertEqual(len(entities), 1)
        self.assertEqual(
            entities[0].entity_type,
            "PHONE",
        )
        self.assertEqual(
            entities[0].risk,
            "amber",
        )

    def test_detects_international_sri_lankan_phone(self):

        text = "Call me on +94 77 123 4567"

        entities = self.detector.detect(text)

        self.assertEqual(len(entities), 1)
        self.assertEqual(
            entities[0].entity_type,
            "PHONE",
        )

    def test_detects_nic_with_context(self):

        text = "My NIC is 200012345678"

        entities = self.detector.detect(text)

        self.assertEqual(len(entities), 1)
        self.assertEqual(
            entities[0].entity_type,
            "NIC",
        )
        self.assertEqual(
            entities[0].risk,
            "amber",
        )

    def test_does_not_assume_any_12_digit_number_is_nic(self):

        text = "The reference number is 200012345678"

        entities = self.detector.detect(text)

        self.assertEqual(
            entities,
            [],
        )


if __name__ == "__main__":
    unittest.main()