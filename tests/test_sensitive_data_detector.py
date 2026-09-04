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


if __name__ == "__main__":
    unittest.main()