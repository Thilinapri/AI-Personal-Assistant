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

    All text must pass through PrivacyGateway before any
    Gemini request is created.
    """

    def __init__(
        self,
        privacy_gateway,
    ):

        if privacy_gateway is None:
            raise ValueError(
                "MemoryEngine requires a PrivacyGateway."
            )

        self.privacy_gateway = privacy_gateway

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
        text,
        current_time,
    ):

        if mode not in (
            "immediate",
            "summary",
        ):
            raise ValueError(
                f"Unsupported memory engine mode: {mode}"
            )

        # Current AudioWorker and SessionProcessor provide
        # newline-separated transcript context.
        #
        # Convert it back to individual local sentences before
        # passing anything through the PrivacyGateway.
        sentences = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

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

            # Privacy components fail closed.
            # Never send raw text as a fallback.
            return self._empty_result(
                mode
            )

        if not privacy_result.cloud_allowed:
            return self._empty_result(
                mode
            )

        # Only the sanitized minimum-disclosure capsule
        # is allowed into the cloud prompt.
        prompt = self.prompt_builder.build(
            mode=mode,
            text=privacy_result.capsule.text,
            current_time=current_time,
        )

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

        # Restore AMBER placeholders only after the
        # cloud response has returned to the local device.
        return self._rehydrate_value(
            result,
            privacy_result.mapping,
        )

    def _rehydrate_value(
        self,
        value,
        mapping,
    ):

        if isinstance(value, str):
            return (
                self.privacy_gateway.rehydrate_output(
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
                for key, item in value.items()
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