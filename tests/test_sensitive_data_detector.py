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

    def test_detects_valid_payment_card_as_red(self):

        text = (
            "My card number is "
            "4111 1111 1111 1111"
        )

        entities = self.detector.detect(text)

        card_entities = [
            entity
            for entity in entities
            if entity.entity_type
            == "PAYMENT_CARD"
        ]

        self.assertEqual(
            len(card_entities),
            1,
        )

        self.assertEqual(
            card_entities[0].risk,
            "red",
        )

    def test_invalid_card_candidate_is_not_flagged(self):

        text = (
            "Reference number "
            "4111 1111 1111 1112"
        )

        entities = self.detector.detect(text)

        card_entities = [
            entity
            for entity in entities
            if entity.entity_type
            == "PAYMENT_CARD"
        ]

        self.assertEqual(
            card_entities,
            [],
        )

    def test_detects_home_address_as_amber(self):

        text = (
            "My home address is "
            "25 Example Road, Colombo."
        )

        entities = self.detector.detect(text)

        address_entities = [
            entity
            for entity in entities
            if entity.entity_type == "ADDRESS"
        ]

        self.assertEqual(
            len(address_entities),
            1,
        )

        self.assertEqual(
            address_entities[0].risk,
            "amber",
        )

    def test_detects_live_at_address_as_amber(self):

        text = (
            "I live at "
            "No. 12/3, Temple Road, Kandy."
        )

        entities = self.detector.detect(text)

        address_entities = [
            entity
            for entity in entities
            if entity.entity_type == "ADDRESS"
        ]

        self.assertEqual(
            len(address_entities),
            1,
        )

        self.assertEqual(
            address_entities[0].risk,
            "amber",
        )

    def test_normal_place_name_is_not_treated_as_private_address(self):

        text = "Meeting at SLIIT tomorrow."

        entities = self.detector.detect(text)

        address_entities = [
            entity
            for entity in entities
            if entity.entity_type == "ADDRESS"
        ]

        self.assertEqual(
            address_entities,
            [],
        )

    def test_detects_card_security_code_as_red(self):

        text = "My CVV is 123"

        entities = self.detector.detect(text)

        security_entities = [
            entity
            for entity in entities
            if entity.entity_type
            == "CARD_SECURITY_CODE"
        ]

        self.assertEqual(
            len(security_entities),
            1,
        )

        self.assertEqual(
            security_entities[0].risk,
            "red",
        )

    def test_random_three_digit_number_is_not_card_security_code(self):

        text = "Room number is 123"

        entities = self.detector.detect(text)

        security_entities = [
            entity
            for entity in entities
            if entity.entity_type
            == "CARD_SECURITY_CODE"
        ]

        self.assertEqual(
            security_entities,
            [],
        )

    def test_detects_passport_number_as_amber(self):

        text = "My passport number is N1234567"

        entities = self.detector.detect(text)

        passport_entities = [
            entity
            for entity in entities
            if entity.entity_type == "PASSPORT"
        ]

        self.assertEqual(
            len(passport_entities),
            1,
        )

        self.assertEqual(
            passport_entities[0].risk,
            "amber",
        )

    def test_booking_reference_is_not_treated_as_passport(self):

        text = "Booking reference is N1234567"

        entities = self.detector.detect(text)

        passport_entities = [
            entity
            for entity in entities
            if entity.entity_type == "PASSPORT"
        ]

        self.assertEqual(
            passport_entities,
            [],
        )

    def test_detects_numeric_date_of_birth_as_amber(self):

        text = "My date of birth is 15/08/2002"

        entities = self.detector.detect(text)

        dob_entities = [
            entity
            for entity in entities
            if entity.entity_type == "DATE_OF_BIRTH"
        ]

        self.assertEqual(
            len(dob_entities),
            1,
        )

        self.assertEqual(
            dob_entities[0].risk,
            "amber",
        )

    def test_detects_spoken_date_of_birth_as_amber(self):

        text = "I was born on 15 August 2002"

        entities = self.detector.detect(text)

        dob_entities = [
            entity
            for entity in entities
            if entity.entity_type == "DATE_OF_BIRTH"
        ]

        self.assertEqual(
            len(dob_entities),
            1,
        )

        self.assertEqual(
            dob_entities[0].risk,
            "amber",
        )

    def test_normal_event_date_is_not_treated_as_date_of_birth(self):

        text = "My presentation is on 15 August 2026"

        entities = self.detector.detect(text)

        dob_entities = [
            entity
            for entity in entities
            if entity.entity_type == "DATE_OF_BIRTH"
        ]

        self.assertEqual(
            dob_entities,
            [],
        )

    def test_detects_precise_gps_coordinates_as_amber(self):

        text = (
            "My GPS coordinates are "
            "6.9271, 79.8612"
        )

        entities = self.detector.detect(text)

        location_entities = [
            entity
            for entity in entities
            if entity.entity_type
            == "PRECISE_LOCATION"
        ]

        self.assertEqual(
            len(location_entities),
            1,
        )

        self.assertEqual(
            location_entities[0].risk,
            "amber",
        )

    def test_coordinates_without_location_context_are_not_flagged(self):

        text = "The values are 6.9271, 79.8612"

        entities = self.detector.detect(text)

        location_entities = [
            entity
            for entity in entities
            if entity.entity_type
            == "PRECISE_LOCATION"
        ]

        self.assertEqual(
            location_entities,
            [],
        )

    def test_invalid_gps_coordinates_are_not_flagged(self):

        text = (
            "GPS coordinates are "
            "95.0000, 200.0000"
        )

        entities = self.detector.detect(text)

        location_entities = [
            entity
            for entity in entities
            if entity.entity_type
            == "PRECISE_LOCATION"
        ]

        self.assertEqual(
            location_entities,
            [],
        )


if __name__ == "__main__":
    unittest.main()