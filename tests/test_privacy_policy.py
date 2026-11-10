import unittest

from src.privacy import (
    PrivacyPolicy,
    SensitiveEntity,
)


class PrivacyPolicyTests(unittest.TestCase):

    def setUp(self):
        self.policy = PrivacyPolicy()

    def test_no_sensitive_data_is_allowed(self):

        decision = self.policy.evaluate([])

        self.assertEqual(
            decision.action,
            "allow",
        )
        self.assertTrue(
            decision.cloud_allowed
        )
        self.assertEqual(
            decision.risk_level,
            "low",
        )

    def test_red_secret_is_blocked(self):

        entities = [
            SensitiveEntity(
                entity_type="PASSWORD",
                start=10,
                end=20,
                risk="red",
            )
        ]

        decision = self.policy.evaluate(
            entities
        )

        self.assertEqual(
            decision.action,
            "block",
        )
        self.assertFalse(
            decision.cloud_allowed
        )
        self.assertEqual(
            decision.risk_level,
            "critical",
        )

    def test_amber_data_requires_sanitization(self):

        entities = [
            SensitiveEntity(
                entity_type="PHONE",
                start=5,
                end=15,
                risk="amber",
            )
        ]

        decision = self.policy.evaluate(
            entities
        )

        self.assertEqual(
            decision.action,
            "sanitize",
        )
        self.assertTrue(
            decision.cloud_allowed
        )
        self.assertEqual(
            decision.risk_level,
            "medium",
        )

    def test_green_data_is_allowed(self):

        entities = [
            SensitiveEntity(
                entity_type="DATE",
                start=5,
                end=15,
                risk="green",
            )
        ]

        decision = self.policy.evaluate(
            entities
        )

        self.assertEqual(
            decision.action,
            "allow",
        )
        self.assertTrue(
            decision.cloud_allowed
        )

    def test_red_overrides_amber(self):

        entities = [
            SensitiveEntity(
                entity_type="PHONE",
                start=0,
                end=10,
                risk="amber",
            ),
            SensitiveEntity(
                entity_type="API_KEY",
                start=20,
                end=40,
                risk="red",
            ),
        ]

        decision = self.policy.evaluate(
            entities
        )

        self.assertEqual(
            decision.action,
            "block",
        )
        self.assertFalse(
            decision.cloud_allowed
        )


if __name__ == "__main__":
    unittest.main()