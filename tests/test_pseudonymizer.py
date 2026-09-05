import unittest

from src.privacy import (
    Pseudonymizer,
    SensitiveDataDetector,
)


class PseudonymizerTests(unittest.TestCase):

    def setUp(self):
        self.detector = SensitiveDataDetector()
        self.pseudonymizer = Pseudonymizer()

    def test_pseudonymizes_email(self):

        text = "Email me at demo.user@example.com"

        entities = self.detector.detect(text)

        result = self.pseudonymizer.pseudonymize(
            text,
            entities,
        )

        self.assertEqual(
            result.text,
            "Email me at <EMAIL_1>",
        )

        self.assertEqual(
            result.mapping["<EMAIL_1>"],
            "demo.user@example.com",
        )

        self.assertIn(
            "EMAIL",
            result.redacted_types,
        )

    def test_pseudonymizes_phone(self):

        text = "Call me on 0771234567"

        entities = self.detector.detect(text)

        result = self.pseudonymizer.pseudonymize(
            text,
            entities,
        )

        self.assertEqual(
            result.text,
            "Call me on <PHONE_1>",
        )

        self.assertEqual(
            result.mapping["<PHONE_1>"],
            "0771234567",
        )

    def test_pseudonymizes_nic_as_id(self):

        text = "My NIC is 200012345678"

        entities = self.detector.detect(text)

        result = self.pseudonymizer.pseudonymize(
            text,
            entities,
        )

        self.assertEqual(
            result.text,
            "My NIC is <ID_1>",
        )

        self.assertEqual(
            result.mapping["<ID_1>"],
            "200012345678",
        )

    def test_pseudonymizes_address(self):

        text = (
            "My home address is "
            "25 Example Road, Colombo."
        )

        entities = self.detector.detect(text)

        result = self.pseudonymizer.pseudonymize(
            text,
            entities,
        )

        self.assertEqual(
            result.text,
            "My home address is <ADDRESS_1>.",
        )

        self.assertEqual(
            result.mapping["<ADDRESS_1>"],
            "25 Example Road, Colombo",
        )

        self.assertIn(
            "ADDRESS",
            result.redacted_types,
        )

    def test_pseudonymizes_passport_as_id(self):

        text = "My passport number is N1234567"

        entities = self.detector.detect(text)

        result = self.pseudonymizer.pseudonymize(
            text,
            entities,
        )

        self.assertEqual(
            result.text,
            "My passport number is <ID_1>",
        )

        self.assertEqual(
            result.mapping["<ID_1>"],
            "N1234567",
        )

        self.assertIn(
            "PASSPORT",
            result.redacted_types,
        )

    def test_rehydrates_passport_locally(self):

        text = "My passport number is N1234567"

        entities = self.detector.detect(text)

        result = self.pseudonymizer.pseudonymize(
            text,
            entities,
        )

        restored = self.pseudonymizer.rehydrate(
            result.text,
            result.mapping,
        )

        self.assertEqual(
            restored,
            text,
        )

    def test_pseudonymizes_date_of_birth(self):

        text = "My date of birth is 15/08/2002"

        entities = self.detector.detect(text)

        result = self.pseudonymizer.pseudonymize(
            text,
            entities,
        )

        self.assertEqual(
            result.text,
            "My date of birth is <DOB_1>",
        )

        self.assertEqual(
            result.mapping["<DOB_1>"],
            "15/08/2002",
        )

        self.assertIn(
            "DATE_OF_BIRTH",
            result.redacted_types,
        )

    def test_rehydrates_date_of_birth_locally(self):

        text = "My date of birth is 15/08/2002"

        entities = self.detector.detect(text)

        result = self.pseudonymizer.pseudonymize(
            text,
            entities,
        )

        restored = self.pseudonymizer.rehydrate(
            result.text,
            result.mapping,
        )

        self.assertEqual(
            restored,
            text,
        )

    def test_pseudonymizes_precise_location(self):

        text = (
            "My GPS coordinates are "
            "6.9271, 79.8612"
        )

        entities = self.detector.detect(text)

        result = self.pseudonymizer.pseudonymize(
            text,
            entities,
        )

        self.assertEqual(
            result.text,
            "My GPS coordinates are <LOCATION_1>",
        )

        self.assertEqual(
            result.mapping["<LOCATION_1>"],
            "6.9271, 79.8612",
        )

        self.assertIn(
            "PRECISE_LOCATION",
            result.redacted_types,
        )

    def test_rehydrates_precise_location_locally(self):

        text = (
            "My GPS coordinates are "
            "6.9271, 79.8612"
        )

        entities = self.detector.detect(text)

        result = self.pseudonymizer.pseudonymize(
            text,
            entities,
        )

        restored = self.pseudonymizer.rehydrate(
            result.text,
            result.mapping,
        )

        self.assertEqual(
            restored,
            text,
        )

    def test_same_value_reuses_same_placeholder(self):

        text = (
            "Email demo@example.com and "
            "later email demo@example.com again."
        )

        entities = self.detector.detect(text)

        result = self.pseudonymizer.pseudonymize(
            text,
            entities,
        )

        self.assertEqual(
            result.text.count("<EMAIL_1>"),
            2,
        )

        self.assertEqual(
            len(result.mapping),
            1,
        )

    def test_rehydrates_placeholders_locally(self):

        text = "Call <PHONE_1> tomorrow."

        mapping = {
            "<PHONE_1>": "0771234567",
        }

        restored = self.pseudonymizer.rehydrate(
            text,
            mapping,
        )

        self.assertEqual(
            restored,
            "Call 0771234567 tomorrow.",
        )

    def test_red_secret_cannot_be_pseudonymized(self):

        text = "My password is DemoPassword123"

        entities = self.detector.detect(text)

        with self.assertRaises(ValueError):
            self.pseudonymizer.pseudonymize(
                text,
                entities,
            )

    def test_result_repr_does_not_expose_mapping_values(self):

        text = "Email me at demo@example.com"

        entities = self.detector.detect(text)

        result = self.pseudonymizer.pseudonymize(
            text,
            entities,
        )

        representation = repr(result)

        self.assertNotIn(
            "demo@example.com",
            representation,
        )


if __name__ == "__main__":
    unittest.main()
    