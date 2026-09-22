import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.ai.prompt_builder import PromptBuilder
from src.config import GEMINI_MODEL


class MemoryEngine:
    """
    Cloud-backed memory extraction engine.

    Privacy Gateway is optional.

    When privacy is enabled:
        sentences
        -> Context Selector inside PrivacyGateway
        -> privacy protection
        -> Gemini

    When privacy is disabled:
        sentences
        -> Context Selector
        -> Gemini
    """

    def __init__(
        self,
        privacy_gateway=None,
        context_selector=None,
    ):

        if (
            privacy_gateway is None
            and context_selector is None
        ):
            raise ValueError(
                "MemoryEngine requires either a "
                "PrivacyGateway or ContextSelector."
            )

        self.privacy_gateway = privacy_gateway
        self.context_selector = context_selector

        load_dotenv()

        api_key = os.getenv(
            "GEMINI_API_KEY"
        )

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found."
            )

        self.client = genai.Client(
            api_key=api_key
        )

        self.prompt_builder = PromptBuilder()

    def process(
        self,
        mode,
        sentences,
        current_time,
    ):

        if mode not in (
            "immediate",
            "summary",
        ):
            raise ValueError(
                f"Unsupported memory engine mode: {mode}"
            )

        sentences = [
            sentence.strip()
            for sentence in sentences
            if (
                isinstance(sentence, str)
                and sentence.strip()
            )
        ]

        if not sentences:
            return self._empty_result(
                mode
            )

        privacy_mode = (
            "immediate"
            if mode == "immediate"
            else "session"
        )

        pinned_original_index = (
            len(sentences) - 1
            if (
                privacy_mode == "immediate"
                and sentences
            )
            else None
        )

        # ---------------------------------
        # Prepare Cloud Context
        # ---------------------------------

        if self.privacy_gateway is not None:

            prepared = self._prepare_with_privacy(
                sentences=sentences,
                mode=mode,
                privacy_mode=privacy_mode,
                pinned_original_index=(
                    pinned_original_index
                ),
            )

            if prepared is None:
                return self._empty_result(
                    mode
                )

            cloud_text = prepared[
                "text"
            ]

            mapping = prepared[
                "mapping"
            ]

            privacy_enabled = True

        else:

            cloud_text = (
                self._prepare_without_privacy(
                    sentences=sentences,
                    privacy_mode=privacy_mode,
                    pinned_original_index=(
                        pinned_original_index
                    ),
                )
            )

            if not cloud_text:
                return self._empty_result(
                    mode
                )

            mapping = {}

            privacy_enabled = False

        # ---------------------------------
        # Build Gemini Prompt
        # ---------------------------------

        prompt = self.prompt_builder.build(
            mode=mode,
            text=cloud_text,
            current_time=current_time,
        )

        # ---------------------------------
        # Gemini Request
        # ---------------------------------

        response = (
            self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type=(
                        "application/json"
                    ),
                ),
            )
        )

        result = json.loads(
            response.text
        )

        # ---------------------------------
        # Privacy Output Validation
        # ---------------------------------

        if privacy_enabled:

            try:
                (
                    output_safe,
                    _detected_types,
                ) = (
                    self.privacy_gateway
                    .validate_cloud_output(
                        result
                    )
                )

            except Exception:

                # Privacy-enabled mode must fail closed.
                return self._empty_result(
                    mode
                )

            if not output_safe:
                return self._empty_result(
                    mode
                )

            # Restore locally pseudonymized values only
            # after the cloud response passes validation.
            result = self._rehydrate_value(
                result,
                mapping,
            )

        return result

    def _prepare_with_privacy(
        self,
        sentences,
        mode,
        privacy_mode,
        pinned_original_index,
    ):
        """
        Prepare context using the complete Privacy Gateway.

        Privacy failures fail closed and prevent cloud access.
        """

        try:
            privacy_result = (
                self.privacy_gateway.prepare(
                    sentences=sentences,
                    mode=privacy_mode,
                    purpose="memory_extraction",
                    pinned_original_index=(
                        pinned_original_index
                    ),
                )
            )

        except Exception:
            return None

        if not privacy_result.cloud_allowed:
            return None

        return {
            "text": (
                privacy_result.capsule.text
            ),
            "mapping": (
                privacy_result.mapping
            ),
        }

    def _prepare_without_privacy(
        self,
        sentences,
        privacy_mode,
        pinned_original_index,
    ):
        """
        Prepare relevant context when Privacy Gateway
        has been disabled.

        Context selection remains active so EchoMind
        still avoids sending obviously irrelevant
        conversation to Gemini.
        """

        try:
            selection = (
                self.context_selector.select(
                    sentences
                )
            )

        except Exception:
            return ""

        selected_by_index = {
            item.original_index: item.text
            for item in (
                selection.selected_items
            )
        }

        # Immediate processing must preserve the latest
        # triggered sentence even if the relevance selector
        # did not independently choose it.
        if (
            privacy_mode == "immediate"
            and pinned_original_index is not None
            and 0
            <= pinned_original_index
            < len(sentences)
        ):
            selected_by_index[
                pinned_original_index
            ] = sentences[
                pinned_original_index
            ]

        selected_sentences = [
            selected_by_index[index]
            for index in sorted(
                selected_by_index
            )
        ]

        return "\n".join(
            selected_sentences
        )

    def _rehydrate_value(
        self,
        value,
        mapping,
    ):

        if isinstance(value, str):
            return (
                self.privacy_gateway
                .rehydrate_output(
                    value,
                    mapping,
                )
            )

        if isinstance(value, list):
            return [
                self._rehydrate_value(
                    item,
                    mapping,
                )
                for item in value
            ]

        if isinstance(value, dict):
            return {
                key: self._rehydrate_value(
                    item,
                    mapping,
                )
                for key, item
                in value.items()
            }

        return value

    @staticmethod
    def _empty_result(
        mode,
    ):

        if mode == "summary":
            return {
                "summary": "",
                "memories": [],
            }

        return {
            "memories": [],
        }