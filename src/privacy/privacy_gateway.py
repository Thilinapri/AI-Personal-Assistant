from dataclasses import dataclass, field

from src.privacy.context_selector import ScoredSentence
from src.privacy.minimum_disclosure import MinimumDisclosureGate
from src.privacy.privacy_capsule import PrivacyCapsule
from src.privacy.privacy_policy import PrivacyPolicy
from src.privacy.pseudonymizer import Pseudonymizer
from src.privacy.sensitive_data_detector import SensitiveDataDetector


@dataclass
class PrivacyGatewayResult:
    """
    Result produced locally by the PrivacyGateway.

    mapping contains AMBER placeholder-to-original-value
    relationships and must remain local only.
    """

    capsule: PrivacyCapsule

    mapping: dict[str, str] = field(
        default_factory=dict,
        repr=False,
    )

    @property
    def cloud_allowed(self):
        return (
            not self.capsule.blocked
            and bool(self.capsule.text.strip())
        )


class PrivacyGateway:
    """
    EchoMind's local privacy boundary.

    Processing order:

    1. Select memory-relevant context locally.
    2. Detect sensitive information.
    3. Apply RED / AMBER / GREEN privacy policy.
    4. Pseudonymize AMBER information locally.
    5. Apply minimum-disclosure limits.
    6. Produce a PrivacyCapsule.

    Raw transcript text must not cross the cloud boundary.
    """

    ITEM_SEPARATOR = "\n<PRIVACY_ITEM_SEPARATOR>\n"

    SAFE_INTENT_PHRASES = (
        "remind me",
        "remember to",
        "don't forget",
        "do not forget",
        "deadline",
        "appointment",
        "meeting",
        "submit",
        "submission",
        "due date",
        "i need to",
        "i have to",
        "i must",
        "call ",
        "send ",
        "pay ",
        "buy ",
        "book ",
        "pick up",
        "change ",
        "rotate ",
        "reset ",
        "renew ",
        "update ",
        "revoke ",
    )

    def __init__(
        self,
        context_selector,
        detector=None,
        policy=None,
        pseudonymizer=None,
        disclosure_gate=None,
        semantic_classifier=None,
    ):
        if context_selector is None:
            raise ValueError(
                "PrivacyGateway requires a ContextSelector."
            )

        self.context_selector = context_selector

        self.detector = (
            detector
            if detector is not None
            else SensitiveDataDetector()
        )

        self.policy = (
            policy
            if policy is not None
            else PrivacyPolicy()
        )

        self.pseudonymizer = (
            pseudonymizer
            if pseudonymizer is not None
            else Pseudonymizer()
        )

        self.disclosure_gate = (
            disclosure_gate
            if disclosure_gate is not None
            else MinimumDisclosureGate()
        )

        self.semantic_classifier = (
            semantic_classifier
        )

    def prepare(
        self,
        sentences,
        mode,
        purpose="memory_extraction",
        pinned_original_index=None,
    ) -> PrivacyGatewayResult:
        """
        Prepare a sanitized minimum-disclosure capsule.

        Nothing returned in capsule.text should be considered
        cloud-approved unless cloud_allowed is True.
        """

        if mode not in ("immediate", "session"):
            raise ValueError(
                f"Unsupported privacy gateway mode: {mode}"
            )

        selection = self.context_selector.select(
            sentences
        )

        if not selection.selected_items:
            return self._blocked_result(
                purpose=purpose,
                risk_level="low",
                original_sentence_count=(
                    selection.original_sentence_count
                ),
                redacted_types=[],
                reason="no_relevant_context",
            )

        protected_items = []
        redacted_red_types = []

        # Process RED information sentence-by-sentence.
        #
        # A RED-only sentence is discarded locally.
        # A sentence containing useful reminder/task intent may
        # continue only after the secret itself has been removed.
        for item in selection.selected_items:

            item_entities = self.detector.detect(
                item.text
            )

            red_entities = [
                entity
                for entity in item_entities
                if entity.risk == "red"
            ]

            if not red_entities:
                protected_items.append(
                    item
                )
                continue

            for entity in red_entities:
                if (
                    entity.entity_type
                    not in redacted_red_types
                ):
                    redacted_red_types.append(
                        entity.entity_type
                    )

            redacted_text = (
                self._redact_red_entities(
                    item.text,
                    red_entities,
                )
            )

            # Fail closed if RED content is still detectable
            # after local redaction.
            remaining_entities = (
                self.detector.detect(
                    redacted_text
                )
            )

            if any(
                entity.risk == "red"
                for entity in remaining_entities
            ):
                return self._blocked_result(
                    purpose=purpose,
                    risk_level="critical",
                    original_sentence_count=(
                        selection.original_sentence_count
                    ),
                    redacted_types=(
                        redacted_red_types
                    ),
                    reason=(
                        "red_secret_remaining_"
                        "after_sanitization"
                    ),
                )

            # Do not send a sentence whose only useful
            # information was the secret itself.
            if not self._has_safe_intent(
                redacted_text
            ):
                continue

            protected_items.append(
                ScoredSentence(
                    text=redacted_text,
                    score=item.score,
                    original_index=(
                        item.original_index
                    ),
                    selection_source=(
                        item.selection_source
                    ),
                )
            )

        if not protected_items:

            reason = (
                "red_secret_only"
                if redacted_red_types
                else "no_relevant_context"
            )

            risk_level = (
                "critical"
                if redacted_red_types
                else "low"
            )

            return self._blocked_result(
                purpose=purpose,
                risk_level=risk_level,
                original_sentence_count=(
                    selection.original_sentence_count
                ),
                redacted_types=(
                    redacted_red_types
                ),
                reason=reason,
            )

        # Detect AMBER information and pseudonymize it
        # before semantic privacy screening.
        #
        # The semantic classifier should never receive
        # exact personal values that we already know
        # how to sanitize deterministically.
        joined_text = self.ITEM_SEPARATOR.join(
            item.text
            for item in protected_items
        )

        entities = self.detector.detect(
            joined_text
        )

        decision = self.policy.evaluate(
            entities
        )

        # RED content should already have been handled
        # sentence-by-sentence above. Keep this as a
        # fail-closed safety barrier.
        if not decision.cloud_allowed:
            return self._blocked_result(
                purpose=purpose,
                risk_level=decision.risk_level,
                original_sentence_count=(
                    selection.original_sentence_count
                ),
                redacted_types=sorted(
                    set(
                        redacted_red_types
                        + self._entity_types(
                            entities
                        )
                    )
                ),
                reason=decision.reason,
            )

        mapping = {}

        redacted_types = list(
            redacted_red_types
        )

        if (
            decision.action
            == PrivacyPolicy.ACTION_SANITIZE
        ):

            pseudonymized = (
                self.pseudonymizer.pseudonymize(
                    joined_text,
                    entities,
                )
            )

            protected_text = (
                pseudonymized.text
            )

            mapping = pseudonymized.mapping

            for entity_type in (
                pseudonymized.redacted_types
            ):
                if (
                    entity_type
                    not in redacted_types
                ):
                    redacted_types.append(
                        entity_type
                    )

        else:
            protected_text = joined_text

        protected_sentences = (
            protected_text.split(
                self.ITEM_SEPARATOR
            )
        )

        if len(protected_sentences) != len(
            protected_items
        ):
            return self._blocked_result(
                purpose=purpose,
                risk_level="critical",
                original_sentence_count=(
                    selection.original_sentence_count
                ),
                redacted_types=redacted_types,
                reason=(
                    "privacy_item_structure_changed"
                ),
            )

        # Rebuild the selected items using the
        # locally sanitized text.
        protected_items = [
            ScoredSentence(
                text=sanitized_text,
                score=item.score,
                original_index=item.original_index,
                selection_source=(
                    item.selection_source
                ),
            )
            for item, sanitized_text in zip(
                protected_items,
                protected_sentences,
            )
        ]

        semantic_filtered = False

        # Optional semantic privacy screening.
        #
        # IMPORTANT:
        # Semantic screening happens AFTER known AMBER
        # values have been pseudonymized. Therefore the
        # classifier receives placeholders such as
        # <EMAIL_1> or <ID_1>, not the original value.
        #
        # SAFE content may continue.
        # UNCERTAIN and SENSITIVE content remain local.
        if self.semantic_classifier is not None:

            try:
                semantic_results = (
                    self.semantic_classifier.classify_many(
                        [
                            item.text
                            for item in protected_items
                        ]
                    )
                )

            except Exception:

                # Privacy components fail closed.
                return self._blocked_result(
                    purpose=purpose,
                    risk_level="critical",
                    original_sentence_count=(
                        selection.original_sentence_count
                    ),
                    redacted_types=(
                        redacted_types
                    ),
                    reason=(
                        "semantic_privacy_"
                        "classifier_error"
                    ),
                )

            if len(semantic_results) != len(
                protected_items
            ):
                return self._blocked_result(
                    purpose=purpose,
                    risk_level="critical",
                    original_sentence_count=(
                        selection.original_sentence_count
                    ),
                    redacted_types=(
                        redacted_types
                    ),
                    reason=(
                        "semantic_privacy_"
                        "result_mismatch"
                    ),
                )

            semantically_safe_items = []

            for item, semantic_result in zip(
                protected_items,
                semantic_results,
            ):

                if semantic_result.cloud_safe:
                    semantically_safe_items.append(
                        item
                    )

                else:
                    semantic_filtered = True

            protected_items = (
                semantically_safe_items
            )

            if not protected_items:
                return self._blocked_result(
                    purpose=purpose,
                    risk_level="medium",
                    original_sentence_count=(
                        selection.original_sentence_count
                    ),
                    redacted_types=(
                        redacted_types
                    ),
                    reason=(
                        "semantic_privacy_blocked"
                    ),
                )

        disclosure = self.disclosure_gate.apply(
            protected_items,
            mode=mode,
            pinned_original_index=(
                pinned_original_index
            ),
        )

        # Final outbound RED safety barrier.
        #
        # Re-scan the exact text that would leave the device.
        # If a critical secret is somehow still detectable,
        # fail closed instead of sending it to the cloud.
        final_entities = self.detector.detect(
            disclosure.text
        )

        final_red_entities = [
            entity
            for entity in final_entities
            if entity.risk == "red"
        ]

        if final_red_entities:

            final_red_types = (
                self._entity_types(
                    final_red_entities
                )
            )

            return self._blocked_result(
                purpose=purpose,
                risk_level="critical",
                original_sentence_count=(
                    selection.original_sentence_count
                ),
                redacted_types=sorted(
                    set(
                        redacted_types
                        + final_red_types
                    )
                ),
                reason=(
                    "red_secret_detected_"
                    "in_final_capsule"
                ),
            )

        # Keep only mappings that are actually present
        # in the final outbound capsule.
        mapping = {
            placeholder: original_value
            for placeholder, original_value
            in mapping.items()
            if placeholder in disclosure.text
        }

        capsule = PrivacyCapsule(
            text=disclosure.text,
            purpose=purpose,
            risk_level=(
                "critical"
                if redacted_red_types
                else (
                    "medium"
                    if semantic_filtered
                    else decision.risk_level
                )
            ),
            original_sentence_count=(
                selection.original_sentence_count
            ),
            selected_sentence_count=(
                disclosure.disclosed_sentence_count
            ),
            redacted_types=redacted_types,
            blocked=False,
            block_reason=None,
        )

        return PrivacyGatewayResult(
            capsule=capsule,
            mapping=mapping,
        )

    def validate_cloud_output(
        self,
        value,
    ):
        """
        Validate Gemini output before local rehydration.

        Any literal sensitive information unexpectedly
        generated by the cloud is rejected before it can
        be restored, stored, or propagated locally.
        """

        detected_types = set()

        for text in self._iter_output_strings(
            value
        ):
            entities = self.detector.detect(
                text
            )

            for entity in entities:
                detected_types.add(
                    entity.entity_type
                )

        return (
            not detected_types,
            sorted(detected_types),
        )

    def _iter_output_strings(
        self,
        value,
    ):
        """
        Yield string values from nested Gemini JSON output.
        """

        if isinstance(value, str):
            yield value
            return

        if isinstance(value, list):
            for item in value:
                yield from self._iter_output_strings(
                    item
                )
            return

        if isinstance(value, dict):
            for item in value.values():
                yield from self._iter_output_strings(
                    item
                )

    def rehydrate_output(
        self,
        text,
        mapping,
    ):
        """
        Restore AMBER placeholders locally after cloud processing.

        RED secrets will never be placed in this mapping.
        """

        return self.pseudonymizer.rehydrate(
            text,
            mapping,
        )

    def _redact_red_entities(
        self,
        text,
        red_entities,
    ):
        """
        Remove RED secrets locally.

        For context-based RED patterns such as PASSWORD or
        API_KEY, the complete sensitive expression is removed.

        Other RED values such as payment-card numbers fall
        back to their detected entity span.

        RED placeholders never receive a rehydration mapping.
        """

        red_types = {
            entity.entity_type
            for entity in red_entities
        }

        replacements = []
        covered_spans = []
        seen_spans = set()

        # RED_PATTERNS provide the complete match, allowing
        # expressions such as "password is Secret123" to be
        # removed rather than only removing "Secret123".
        for entity_type, pattern in (
            self.detector.RED_PATTERNS
        ):

            if entity_type not in red_types:
                continue

            for match in pattern.finditer(
                text
            ):

                start, end = match.span(0)

                span = (
                    start,
                    end,
                )

                if span in seen_spans:
                    continue

                seen_spans.add(
                    span
                )

                covered_spans.append(
                    span
                )

                replacements.append(
                    (
                        start,
                        end,
                        (
                            f"<REDACTED_"
                            f"{entity_type}>"
                        ),
                    )
                )

        # Some RED detectors, such as payment-card Luhn
        # detection, are not part of RED_PATTERNS.
        # Fall back to their exact entity spans.
        for entity in red_entities:

            already_covered = any(
                start <= entity.start
                and entity.end <= end
                for start, end
                in covered_spans
            )

            if already_covered:
                continue

            span = (
                entity.start,
                entity.end,
            )

            if span in seen_spans:
                continue

            seen_spans.add(
                span
            )

            replacements.append(
                (
                    entity.start,
                    entity.end,
                    (
                        f"<REDACTED_"
                        f"{entity.entity_type}>"
                    ),
                )
            )

        result = text

        # Right-to-left replacement keeps earlier offsets valid.
        for start, end, replacement in sorted(
            replacements,
            key=lambda item: item[0],
            reverse=True,
        ):
            result = (
                result[:start]
                + replacement
                + result[end:]
            )

        return result

    @classmethod
    def _has_safe_intent(
        cls,
        text,
    ):
        """
        Decide whether useful non-secret task/reminder intent
        remains after RED information has been removed.

        This deliberately uses cheap string checks rather than
        another MiniLM inference.
        """

        lowered = text.lower()

        return any(
            phrase in lowered
            for phrase in cls.SAFE_INTENT_PHRASES
        )

    @staticmethod
    def _entity_types(
        entities,
    ):
        return sorted(
            {
                entity.entity_type
                for entity in entities
            }
        )

    @staticmethod
    def _blocked_result(
        purpose,
        risk_level,
        original_sentence_count,
        redacted_types,
        reason,
    ):
        capsule = PrivacyCapsule(
            text="",
            purpose=purpose,
            risk_level=risk_level,
            original_sentence_count=(
                original_sentence_count
            ),
            selected_sentence_count=0,
            redacted_types=redacted_types,
            blocked=True,
            block_reason=reason,
        )

        return PrivacyGatewayResult(
            capsule=capsule,
            mapping={},
        )