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

    def test_detects_numeric_password_in_natural_speech(self):

        samples = [
            "My password 4826",
            "The password 7712",
            "My passcode 123456",
        ]

        for text in samples:

            entities = self.detector.detect(text)

            password_entities = [
                entity
                for entity in entities
                if entity.entity_type == "PASSWORD"
            ]

            self.assertEqual(
                len(password_entities),
                1,
                msg=text,
            )

            self.assertEqual(
                password_entities[0].risk,
                "red",
            )

    def test_detects_pin_without_separator_word(self):

        samples = [
            "My PIN 4826",
            "My PIN code 7712",
            "My PIN number 123456",
        ]

        for text in samples:

            entities = self.detector.detect(text)

            pin_entities = [
                entity
                for entity in entities
                if entity.entity_type == "PIN"
            ]

            self.assertEqual(
                len(pin_entities),
                1,
                msg=text,
            )

            self.assertEqual(
                pin_entities[0].risk,
                "red",
            )

    def test_random_four_digit_number_is_not_password_or_pin(self):

        text = "The room number is 4826."

        entities = self.detector.detect(text)

        secret_types = {
            entity.entity_type
            for entity in entities
            if entity.entity_type in {
                "PASSWORD",
                "PIN",
            }
        }

        self.assertEqual(
            secret_types,
            set(),
        )

    def test_password_policy_is_not_treated_as_secret(self):

        text = (
            "The password policy review "
            "is on Friday."
        )

        entities = self.detector.detect(text)

        password_entities = [
            entity
            for entity in entities
            if entity.entity_type == "PASSWORD"
        ]

        self.assertEqual(
            password_entities,
            [],
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

    def test_detects_jwt_token_without_context(self):

        text = (
            "eyJhbGciOiJIUzI1NiJ9."
            "eyJ1c2VyIjoiMTIzIn0."
            "demoSignature123"
        )

        entities = self.detector.detect(text)

        jwt_entities = [
            entity
            for entity in entities
            if entity.entity_type == "JWT_TOKEN"
        ]

        self.assertEqual(
            len(jwt_entities),
            1,
        )

        self.assertEqual(
            jwt_entities[0].risk,
            "red",
        )

        self.assertEqual(
            text[
                jwt_entities[0].start:
                jwt_entities[0].end
            ],
            text,
        )

    def test_arbitrary_dot_separated_value_is_not_jwt(self):

        text = "The version is abc.def.xyz."

        entities = self.detector.detect(text)

        jwt_entities = [
            entity
            for entity in entities
            if entity.entity_type == "JWT_TOKEN"
        ]

        self.assertEqual(
            jwt_entities,
            [],
        )

    def test_detects_jwt_without_token_keyword(self):

        text = (
            "Use "
            "eyJhbGciOiJIUzI1NiJ9."
            "eyJ1c2VyIjoiMTIzNDU2In0."
            "demoSignature12345"
            " for the request."
        )

        entities = self.detector.detect(text)

        jwt_entities = [
            entity
            for entity in entities
            if entity.entity_type == "JWT_TOKEN"
        ]

        self.assertEqual(
            len(jwt_entities),
            1,
        )

        self.assertEqual(
            jwt_entities[0].risk,
            "red",
        )

    def test_jwt_is_not_duplicated_as_unknown_identifier(self):

        text = (
            "Use "
            "eyJhbGciOiJIUzI1NiJ9."
            "eyJ1c2VyIjoiMTIzNDU2In0."
            "demoSignature12345"
        )

        entities = self.detector.detect(text)

        entity_types = [
            entity.entity_type
            for entity in entities
        ]

        self.assertIn(
            "JWT_TOKEN",
            entity_types,
        )

        self.assertNotIn(
            "UNKNOWN_IDENTIFIER",
            entity_types,
        )

    def test_normal_dotted_text_is_not_treated_as_jwt(self):

        samples = [
            "The software version is 1.2.3.",
            "Visit docs.example.com for information.",
            "The filename is report.final.pdf.",
            "The value abc.def.xyz is just an example.",
        ]

        for text in samples:

            entities = self.detector.detect(text)

            jwt_entities = [
                entity
                for entity in entities
                if entity.entity_type == "JWT_TOKEN"
            ]

            self.assertEqual(
                jwt_entities,
                [],
                msg=text,
            )

    def test_incomplete_jwt_shape_is_not_flagged(self):

        text = (
            "The example value is "
            "eyJabc.defghi"
        )

        entities = self.detector.detect(text)

        jwt_entities = [
            entity
            for entity in entities
            if entity.entity_type == "JWT_TOKEN"
        ]

        self.assertEqual(
            jwt_entities,
            [],
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

    def test_detects_home_address_with_spoken_at_as_amber(
        self,
    ):

        text = (
            "My home address is at "
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

    def test_detects_api_key_without_separator_in_natural_speech(self):

        text = (
            "Remind me Friday to rotate "
            "API key ABCDEFGHIJK"
        )

        entities = self.detector.detect(text)

        api_key_entities = [
            entity
            for entity in entities
            if entity.entity_type == "API_KEY"
        ]

        self.assertEqual(
            len(api_key_entities),
            1,
        )

        self.assertEqual(
            api_key_entities[0].risk,
            "red",
        )

    def test_detects_unknown_identifier_as_amber(self):

        text = "Use XJ84922018 for the application."

        entities = self.detector.detect(text)

        unknown_entities = [
            entity
            for entity in entities
            if entity.entity_type
            == "UNKNOWN_IDENTIFIER"
        ]

        self.assertEqual(
            len(unknown_entities),
            1,
        )

        self.assertEqual(
            unknown_entities[0].risk,
            "amber",
        )

        self.assertEqual(
            text[
                unknown_entities[0].start:
                unknown_entities[0].end
            ],
            "XJ84922018",
        )

    def test_detects_hyphenated_unknown_identifier(self):

        text = "Use EMP-882731 for the record."

        entities = self.detector.detect(text)

        unknown_entities = [
            entity
            for entity in entities
            if entity.entity_type
            == "UNKNOWN_IDENTIFIER"
        ]

        self.assertEqual(
            len(unknown_entities),
            1,
        )

    def test_known_passport_is_not_duplicated_as_unknown(self):

        text = "My passport number is N1234567"

        entities = self.detector.detect(text)

        entity_types = [
            entity.entity_type
            for entity in entities
        ]

        self.assertIn(
            "PASSPORT",
            entity_types,
        )

        self.assertNotIn(
            "UNKNOWN_IDENTIFIER",
            entity_types,
        )

    def test_common_alphanumeric_terms_are_not_unknown_identifiers(self):

        samples = [
            "Meet me in Room101 tomorrow.",
            "We are using Python314 for testing.",
            "The build is Version123.",
            "Course module ABC1234 starts Monday.",
            "The project is Phase123.",
        ]

        for text in samples:

            entities = self.detector.detect(text)

            unknown_entities = [
                entity
                for entity in entities
                if entity.entity_type
                == "UNKNOWN_IDENTIFIER"
            ]

            self.assertEqual(
                unknown_entities,
                [],
                msg=text,
            )

    def test_normal_sentence_is_not_unknown_identifier(self):

        text = (
            "The project meeting is tomorrow."
        )

        entities = self.detector.detect(text)

        unknown_entities = [
            entity
            for entity in entities
            if entity.entity_type
            == "UNKNOWN_IDENTIFIER"
        ]

        self.assertEqual(
            unknown_entities,
            [],
        )


if __name__ == "__main__":
    unittest.main()