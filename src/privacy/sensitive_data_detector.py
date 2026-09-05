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
    Lightweight local detector for sensitive data.

    RED:
        High-risk secrets that must never be sent to Gemini
        in raw form.

    AMBER:
        Personal information that should be sanitized or
        pseudonymized before cloud processing.
    """

    CARD_CANDIDATE_PATTERN = re.compile(
        r"(?<!\d)("
        r"\d(?:[ -]?\d){12,18}"
        r")(?!\d)"
    )

    PRECISE_LOCATION_PATTERN = re.compile(
        r"\b(?:"
        r"gps(?:\s+coordinates)?"
        r"|coordinates"
        r"|location\s+coordinates"
        r")\b"
        r"\s*(?:are|is|=|:)?\s*"
        r"("
        r"\(?\s*"
        r"-?\d{1,2}\.\d{3,}"
        r"\s*,\s*"
        r"-?\d{1,3}\.\d{3,}"
        r"\s*\)?"
        r")",
        re.IGNORECASE,
    )

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
            "CARD_SECURITY_CODE",
            re.compile(
                r"\b(?:cvv|cvc|card\s+security\s+code|security\s+code)\b"
                r"\s*(?:is|=|:)?\s*"
                r"(\d{3,4})\b",
                re.IGNORECASE,
            ),
        ),
        (
            "API_KEY",
            re.compile(
                r"\b(?:api[_ -]?key|access[_ -]?token|auth[_ -]?token)\b"
                r"\s*(?:is|=|:)?\s*"
                r"[\"']?([A-Za-z0-9._~+\-/=]{8,}?)"
                r"(?=[\s.,!?;]|$)",
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

    AMBER_PATTERNS = (
        (
            "EMAIL",
            re.compile(
                r"\b("
                r"[A-Z0-9._%+-]+"
                r"@"
                r"[A-Z0-9.-]+"
                r"\.[A-Z]{2,}"
                r")\b",
                re.IGNORECASE,
            ),
        ),
        (
            "PHONE",
            re.compile(
                r"(?<!\d)("
                r"(?:\+94|0094|94)[\s-]?7\d"
                r"[\s-]?\d{3}[\s-]?\d{4}"
                r"|"
                r"07\d[\s-]?\d{3}[\s-]?\d{4}"
                r")(?!\d)"
            ),
        ),
        (
            "NIC",
            re.compile(
                r"\b(?:"
                r"nic"
                r"|national\s+(?:identity|id)"
                r"(?:\s+(?:number|no))?"
                r"|identity\s+card"
                r"(?:\s+(?:number|no))?"
                r")\b"
                r"\s*(?:is|=|:)?\s*"
                r"("
                r"\d{9}[VvXx]"
                r"|"
                r"\d{12}"
                r")\b",
                re.IGNORECASE,
            ),
        ),
        (
            "PASSPORT",
            re.compile(
                r"\bpassport"
                r"(?:\s+(?:number|no))?"
                r"\b"
                r"\s*(?:is|=|:)?\s*"
                r"([A-Z0-9]{6,12})\b",
                re.IGNORECASE,
            ),
        ),
        (
            "DATE_OF_BIRTH",
            re.compile(
                r"\b(?:dob|date\s+of\s+birth)\b"
                r"\s*(?:is|=|:)?\s*"
                r"("
                r"(?:0?[1-9]|[12]\d|3[01])"
                r"[./\-]"
                r"(?:0?[1-9]|1[0-2])"
                r"[./\-]"
                r"(?:19|20)\d{2}"
                r")\b",
                re.IGNORECASE,
            ),
        ),
        (
            "DATE_OF_BIRTH",
            re.compile(
                r"\b(?:dob|date\s+of\s+birth|born\s+on)\b"
                r"\s*(?:is|=|:)?\s*"
                r"("
                r"(?:0?[1-9]|[12]\d|3[01])"
                r"\s+"
                r"(?:"
                r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|"
                r"apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
                r"aug(?:ust)?|sep(?:tember)?|sept(?:ember)?|"
                r"oct(?:ober)?|nov(?:ember)?|dec(?:ember)?"
                r")"
                r"\s+"
                r"(?:19|20)\d{2}"
                r")\b",
                re.IGNORECASE,
            ),
        ),
        (
            "ADDRESS",
            re.compile(
                r"\b(?:home|work|office|residential|postal|mailing)"
                r"\s+address\b"
                r"\s*(?:is|=|:)?\s*"
                r"("
                r"(?:no\.?\s*)?"
                r"\d{1,5}[A-Za-z]?"
                r"(?:[/\-]\d{1,5}[A-Za-z]?)?"
                r"[\s,]+"
                r"[A-Za-z0-9][A-Za-z0-9 .,'\-]{2,80}?"
                r"\b(?:road|rd|street|st|avenue|ave|lane|ln|"
                r"mawatha|place|drive|dr|garden|gardens|terrace)"
                r"(?:[\s,]+[A-Za-z][A-Za-z '\-]{1,40})?"
                r")"
                r"(?=[.!?;]|$)",
                re.IGNORECASE,
            ),
        ),
        (
            "ADDRESS",
            re.compile(
                r"\b(?:i\s+live|i\s+stay|we\s+live|we\s+stay)"
                r"\s+at\s+"
                r"("
                r"(?:no\.?\s*)?"
                r"\d{1,5}[A-Za-z]?"
                r"(?:[/\-]\d{1,5}[A-Za-z]?)?"
                r"[\s,]+"
                r"[A-Za-z0-9][A-Za-z0-9 .,'\-]{2,80}?"
                r"\b(?:road|rd|street|st|avenue|ave|lane|ln|"
                r"mawatha|place|drive|dr|garden|gardens|terrace)"
                r"(?:[\s,]+[A-Za-z][A-Za-z '\-]{1,40})?"
                r")"
                r"(?=[.!?;]|$)",
                re.IGNORECASE,
            ),
        ),
    )

    def detect(self, text: str) -> list[SensitiveEntity]:
        """
        Detect RED and AMBER sensitive entities.

        The sensitive values themselves are not copied into
        returned metadata objects.
        """

        if not text or not text.strip():
            return []

        entities = []

        self._detect_patterns(
            text=text,
            patterns=self.RED_PATTERNS,
            risk="red",
            entities=entities,
        )

        self._detect_card_numbers(
            text=text,
            entities=entities,
        )

        self._detect_precise_locations(
            text=text,
            entities=entities,
        )

        self._detect_patterns(
            text=text,
            patterns=self.AMBER_PATTERNS,
            risk="amber",
            entities=entities,
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

        return any(
            entity.risk == "red"
            for entity in self.detect(text)
        )

    @staticmethod
    def _detect_patterns(
        text,
        patterns,
        risk,
        entities,
    ):
        """Apply one group of patterns to text."""

        for entity_type, pattern in patterns:

            for match in pattern.finditer(text):

                start, end = match.span(1)

                entities.append(
                    SensitiveEntity(
                        entity_type=entity_type,
                        start=start,
                        end=end,
                        risk=risk,
                    )
                )

    def _detect_card_numbers(
        self,
        text,
        entities,
    ):
        """
        Detect payment-card candidates only when they
        pass the Luhn checksum.
        """

        for match in self.CARD_CANDIDATE_PATTERN.finditer(
            text
        ):

            candidate = match.group(1)

            digits = re.sub(
                r"\D",
                "",
                candidate,
            )

            if not 13 <= len(digits) <= 19:
                continue

            if not self._passes_luhn(digits):
                continue

            start, end = match.span(1)

            entities.append(
                SensitiveEntity(
                    entity_type="PAYMENT_CARD",
                    start=start,
                    end=end,
                    risk="red",
                )
            )

    @staticmethod
    def _passes_luhn(
        digits,
    ):
        """
        Validate a numeric string using the Luhn checksum.
        """

        if not digits.isdigit():
            return False

        total = 0
        reverse_digits = digits[::-1]

        for index, digit in enumerate(
            reverse_digits
        ):
            value = int(digit)

            if index % 2 == 1:
                value *= 2

                if value > 9:
                    value -= 9

            total += value

        return total % 10 == 0

    def _detect_precise_locations(
        self,
        text,
        entities,
    ):
        """
        Detect precise latitude/longitude pairs only when
        explicit GPS/location context is present.
        """

        for match in self.PRECISE_LOCATION_PATTERN.finditer(
            text
        ):

            candidate = match.group(1)

            numbers = re.findall(
                r"-?\d+(?:\.\d+)?",
                candidate,
            )

            if len(numbers) != 2:
                continue

            latitude = float(numbers[0])
            longitude = float(numbers[1])

            if not -90 <= latitude <= 90:
                continue

            if not -180 <= longitude <= 180:
                continue

            start, end = match.span(1)

            entities.append(
                SensitiveEntity(
                    entity_type="PRECISE_LOCATION",
                    start=start,
                    end=end,
                    risk="amber",
                )
            )

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