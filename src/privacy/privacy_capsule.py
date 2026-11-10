from dataclasses import dataclass, field


@dataclass
class PrivacyCapsule:
    """
    Represents the sanitized and minimized information that is
    allowed to cross EchoMind's local privacy boundary.

    Raw conversational content must not be sent to a cloud
    service unless it has first been transformed into a
    PrivacyCapsule by the PrivacyGateway.
    """

    text: str
    purpose: str
    risk_level: str

    original_sentence_count: int
    selected_sentence_count: int

    redacted_types: list[str] = field(
        default_factory=list
    )

    blocked: bool = False
    block_reason: str | None = None