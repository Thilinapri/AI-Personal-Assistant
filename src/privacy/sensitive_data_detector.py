from dataclasses import dataclass
import re


@dataclass(frozen=True)
class SensitiveEntity:
    """
    Describes sensitive content detected inside text.

    The actual sensitive value is NOT stored here.
    Only the type, position, and risk level are retained.
    """

    entity_type: str
    start: int
    end: int
    risk: str


class SensitiveDataDetector:
    """
    Lightweight local detector for high-risk sensitive data.

    This first version focuses only on RED-category secrets
    that should never be sent to Gemini in raw form.
    """

    RED_PATTERNS = (
        (
            "PASSWORD",
            re.compile(
                r"\b(?:password|passcode)\b"
                r"\s*(?:is|=|:)\s*"
                r"[\"']?([^\s,\"';]+)",
                re.IGNORECASE,
            ),
        ),
        (
            "PIN",
            re.compile(
                r"\bpin(?:\s+(?:code|number))?\b"
                r"\s*(?:is|=|:)\s*"
                r"[\"']?(\d{4,8})\b",
                re.IGNORECASE,
            ),
        ),
        (
            "API_KEY",
            re.compile(
                r"\b(?:api[_ -]?key|access[_ -]?token|auth[_ -]?token)\b"
                r"\s*(?:is|=|:)\s*"
                r"[\"']?([A-Za-z0-9._~+\-/=]{8,})",
                re.IGNORECASE,
            ),
        ),
        (
            "BEARER_TOKEN",
            re.compile(
                r"\bbearer\s+"
                r"([A-Za-z0-9._~+\-/=]{8,})",
                re.IGNORECASE,
            ),
        ),
    )

    def detect(self, text: str) -> list[SensitiveEntity]:
        """
        Detect RED-category secrets in text.

        Sensitive values themselves are not copied into
        the returned metadata objects.
        """

        if not text or not text.strip():
            return []

        entities = []

        for entity_type, pattern in self.RED_PATTERNS:

            for match in pattern.finditer(text):

                start, end = match.span(1)

                entities.append(
                    SensitiveEntity(
                        entity_type=entity_type,
                        start=start,
                        end=end,
                        risk="red",
                    )
                )

        entities.sort(
            key=lambda entity: (
                entity.start,
                entity.end,
                entity.entity_type,
            )
        )

        return self._remove_duplicates(entities)

    def has_red_secret(self, text: str) -> bool:
        """Return True if at least one RED secret is detected."""

        return bool(self.detect(text))

    @staticmethod
    def _remove_duplicates(
        entities: list[SensitiveEntity],
    ) -> list[SensitiveEntity]:

        unique = []
        seen = set()

        for entity in entities:

            key = (
                entity.entity_type,
                entity.start,
                entity.end,
            )

            if key in seen:
                continue

            seen.add(key)
            unique.append(entity)

        return unique