import json
import os
import random
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
import httpx

from src.ai.prompt_builder import PromptBuilder
from src.ai.openrouter_client import OpenRouterClient
from src.config import (
    GEMINI_MODEL,
    GEMINI_REQUEST_TIMEOUT_MS,
    MEMORY_LLM_PROVIDER,
)


class MemoryEngine:
    """Cloud-backed memory extraction engine.

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

    GEMINI_MAX_ATTEMPTS = 3
    GEMINI_RETRY_BASE_DELAY_SECONDS = 0.5
    GEMINI_RETRY_MAX_DELAY_SECONDS = 3.0
    GEMINI_RETRY_JITTER_SECONDS = 0.25
    GEMINI_RETRYABLE_HTTP_STATUSES = {
        408,
        429,
        500,
        502,
        503,
        504,
        529,
    }

    def __init__(
        self,
        privacy_gateway=None,
        context_selector=None,
        provider=None,
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
        self.provider = (
            provider
            if provider is not None
            else MEMORY_LLM_PROVIDER
        )

        if not isinstance(self.provider, str):
            raise ValueError(
                "Unsupported memory LLM provider."
            )

        self.provider = self.provider.strip().lower()

        if self.provider not in (
            "gemini",
            "openrouter",
        ):
            raise ValueError(
                "Unsupported memory LLM provider."
            )

        load_dotenv()

        if self.provider == "gemini":

            api_key = os.getenv(
                "GEMINI_API_KEY"
            )

            if not api_key:
                raise ValueError(
                    "GEMINI_API_KEY not found."
                )

            self.client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(
                    timeout=GEMINI_REQUEST_TIMEOUT_MS,
                    retry_options=types.HttpRetryOptions(
                        # Retries are handled below so each attempt has
                        # one bounded SDK request and one clear log entry.
                        attempts=1,
                    ),
                ),
            )

        else:

            self.client = OpenRouterClient()

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
        # Build Provider Prompt
        # ---------------------------------

        prompt = self.prompt_builder.build(
            mode=mode,
            text=cloud_text,
            current_time=current_time,
        )

        # ---------------------------------
        # Provider Request
        # ---------------------------------

        if self.provider == "gemini":

            response = self._generate_gemini_content(
                mode=mode,
                prompt=prompt,
            )

            response_text = response.text

        else:

            response_text = (
                self.client.generate_text(
                    prompt
                )
            )

        try:
            result = json.loads(
                response_text
            )

        except (
            json.JSONDecodeError,
            TypeError,
        ):
            raise ValueError(
                "Invalid JSON returned by the memory provider."
            ) from None

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

    def _generate_gemini_content(self, mode, prompt):
        """Make bounded, timed Gemini attempts without logging prompt data."""

        for attempt in range(1, self.GEMINI_MAX_ATTEMPTS + 1):
            print(
                "[MEMORY] Gemini request started "
                f"(mode={mode}, attempt={attempt}/"
                f"{self.GEMINI_MAX_ATTEMPTS})."
            )
            try:
                response = self.client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        response_mime_type="application/json",
                    ),
                )
                print(
                    "[MEMORY] Gemini response received "
                    f"(mode={mode}, attempt={attempt})."
                )
                return response
            except Exception as error:
                category = self._transient_gemini_failure_category(error)
                if category is None:
                    print(
                        "[MEMORY] Gemini request failed "
                        f"(mode={mode}, attempt={attempt}, "
                        f"category={self._safe_failure_category(error)}); "
                        "not retrying."
                    )
                    raise

                if attempt >= self.GEMINI_MAX_ATTEMPTS:
                    print(
                        "[MEMORY] Gemini request failed after "
                        f"{attempt} attempts "
                        f"(mode={mode}, category={category})."
                    )
                    raise

                delay = min(
                    self.GEMINI_RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1)),
                    self.GEMINI_RETRY_MAX_DELAY_SECONDS,
                ) + random.uniform(0, self.GEMINI_RETRY_JITTER_SECONDS)
                print(
                    "[MEMORY] Gemini temporary failure; retrying "
                    f"(mode={mode}, attempt={attempt}/"
                    f"{self.GEMINI_MAX_ATTEMPTS}, category={category}, "
                    f"delay={delay:.2f}s)."
                )
                time.sleep(delay)

        raise RuntimeError("Gemini request attempts exhausted.")

    @staticmethod
    def _transient_gemini_failure_category(error):
        if isinstance(error, genai_errors.APIError):
            try:
                status = int(error.code)
            except (TypeError, ValueError):
                return None
            if status in MemoryEngine.GEMINI_RETRYABLE_HTTP_STATUSES:
                return f"http_{status}"
            return None

        if isinstance(error, httpx.TimeoutException):
            return "timeout"
        if isinstance(error, httpx.TransportError):
            return "network"
        return None

    @staticmethod
    def _safe_failure_category(error):
        if isinstance(error, genai_errors.APIError):
            try:
                return f"http_{int(error.code)}"
            except (TypeError, ValueError):
                return "api_error"
        if isinstance(error, httpx.TimeoutException):
            return "timeout"
        if isinstance(error, httpx.TransportError):
            return "network"
        return type(error).__name__

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
