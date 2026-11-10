from dataclasses import dataclass


@dataclass(frozen=True)
class PrivacyDecision:
    """
    Represents the privacy policy decision for a piece of text.

    cloud_allowed indicates whether processing may continue
    toward a cloud service after all required protections
    have been applied.
    """

    action: str
    risk_level: str
    cloud_allowed: bool
    reason: str


class PrivacyPolicy:
    """
    Converts detected sensitive entities into a privacy action.

    RED    -> BLOCK
    AMBER  -> SANITIZE
    GREEN  -> ALLOW
    NONE   -> ALLOW
    """

    ACTION_ALLOW = "allow"
    ACTION_SANITIZE = "sanitize"
    ACTION_BLOCK = "block"

    def evaluate(self, entities) -> PrivacyDecision:
        """
        Evaluate sensitive-entity metadata and return
        the required privacy action.
        """

        if not entities:
            return PrivacyDecision(
                action=self.ACTION_ALLOW,
                risk_level="low",
                cloud_allowed=True,
                reason="no_sensitive_data_detected",
            )

        risks = {
            entity.risk.lower()
            for entity in entities
        }

        # RED always wins.
        if "red" in risks:
            return PrivacyDecision(
                action=self.ACTION_BLOCK,
                risk_level="critical",
                cloud_allowed=False,
                reason="red_secret_detected",
            )

        # AMBER may continue only after sanitization.
        if "amber" in risks:
            return PrivacyDecision(
                action=self.ACTION_SANITIZE,
                risk_level="medium",
                cloud_allowed=True,
                reason="personal_data_requires_sanitization",
            )

        # GREEN information is considered safe enough
        # to remain when it is relevant to the task.
        return PrivacyDecision(
            action=self.ACTION_ALLOW,
            risk_level="low",
            cloud_allowed=True,
            reason="allowed_information_only",
        )