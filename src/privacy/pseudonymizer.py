from dataclasses import dataclass, field

from src.privacy.sensitive_data_detector import SensitiveEntity


@dataclass
class PseudonymizationResult:
    """
    Result of locally pseudonymizing AMBER personal data.

    mapping contains the temporary placeholder-to-original-value
    relationship. repr=False prevents the sensitive mapping from
    appearing if this object is accidentally printed.
    """

    text: str
    mapping: dict[str, str] = field(repr=False)
    redacted_types: list[str] = field(default_factory=list)


class Pseudonymizer:
    """
    Replaces AMBER personal information with local placeholders.

    RED secrets are not pseudonymized. They must be blocked by
    the privacy policy instead.
    """

    PLACEHOLDER_TYPES = {
        "EMAIL": "EMAIL",
        "PHONE": "PHONE",
        "NIC": "ID",
    }

    def pseudonymize(
        self,
        text: str,
        entities: list[SensitiveEntity],
    ) -> PseudonymizationResult:

        if not text:
            return PseudonymizationResult(
                text="",
                mapping={},
                redacted_types=[],
            )

        if any(entity.risk == "red" for entity in entities):
            raise ValueError(
                "RED secrets must be blocked, not pseudonymized."
            )

        amber_entities = sorted(
            (
                entity
                for entity in entities
                if entity.risk == "amber"
            ),
            key=lambda entity: (
                entity.start,
                entity.end,
            ),
        )

        counters = {}
        value_to_placeholder = {}
        mapping = {}
        replacements = []
        redacted_types = []

        for entity in amber_entities:

            if (
                entity.start < 0
                or entity.end > len(text)
                or entity.start >= entity.end
            ):
                raise ValueError(
                    "Sensitive entity contains invalid text positions."
                )

            original_value = text[
                entity.start:entity.end
            ]

            placeholder_type = self.PLACEHOLDER_TYPES.get(
                entity.entity_type,
                entity.entity_type,
            )

            existing_placeholder = value_to_placeholder.get(
                (
                    entity.entity_type,
                    original_value,
                )
            )

            if existing_placeholder:
                placeholder = existing_placeholder
            else:
                counters[placeholder_type] = (
                    counters.get(
                        placeholder_type,
                        0,
                    )
                    + 1
                )

                placeholder = (
                    f"<{placeholder_type}_"
                    f"{counters[placeholder_type]}>"
                )

                value_to_placeholder[
                    (
                        entity.entity_type,
                        original_value,
                    )
                ] = placeholder

                mapping[placeholder] = original_value

            replacements.append(
                (
                    entity.start,
                    entity.end,
                    placeholder,
                )
            )

            if entity.entity_type not in redacted_types:
                redacted_types.append(
                    entity.entity_type
                )

        pseudonymized_text = text

        # Replace from right to left so earlier character
        # positions remain valid.
        for start, end, placeholder in reversed(
            replacements
        ):
            pseudonymized_text = (
                pseudonymized_text[:start]
                + placeholder
                + pseudonymized_text[end:]
            )

        return PseudonymizationResult(
            text=pseudonymized_text,
            mapping=mapping,
            redacted_types=redacted_types,
        )

    @staticmethod
    def rehydrate(
        text: str,
        mapping: dict[str, str],
    ) -> str:
        """
        Restore placeholders locally after cloud processing.
        """

        restored_text = text

        for placeholder, original_value in mapping.items():
            restored_text = restored_text.replace(
                placeholder,
                original_value,
            )

        return restored_text