import os
from typing import Optional

import requests
from dotenv import load_dotenv

from src.config import OPENROUTER_MODEL


class OpenRouterClientError(RuntimeError):
    """Safe exception for OpenRouter client failures."""


class OpenRouterClient:
    """Small HTTP client for OpenRouter chat-completion requests."""

    ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 30.0,
        session: Optional[requests.Session] = None,
    ):
        load_dotenv()

        resolved_api_key = api_key
        if resolved_api_key is None:
            resolved_api_key = os.getenv("OPENROUTER_API_KEY")

        if not resolved_api_key or not resolved_api_key.strip():
            raise OpenRouterClientError(
                "OpenRouter API key is not configured."
            )

        resolved_model = model
        if resolved_model is None:
            resolved_model = OPENROUTER_MODEL

        if not resolved_model or not resolved_model.strip():
            raise OpenRouterClientError(
                "OpenRouter model is not configured."
            )

        self.api_key = resolved_api_key.strip()
        self.model = resolved_model.strip()
        self.timeout = timeout
        self.session = (
            session
            if session is not None
            else requests.Session()
        )

    def generate_text(self, prompt: str) -> str:
        if not isinstance(prompt, str) or not prompt.strip():
            raise OpenRouterClientError(
                "Prompt must be a non-empty string."
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0.2,
            "response_format": {
                "type": "json_object"
            },
            "provider": {
                "data_collection": "deny",
                "require_parameters": True,
            },
        }

        try:
            response = self.session.post(
                self.ENDPOINT,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )

        except requests.Timeout:
            raise OpenRouterClientError(
                "OpenRouter request timed out."
            ) from None

        except requests.RequestException:
            raise OpenRouterClientError(
                "OpenRouter request failed."
            ) from None

        try:
            response.raise_for_status()

        except requests.HTTPError:
            raise OpenRouterClientError(
                f"OpenRouter returned HTTP status "
                f"{response.status_code}."
            ) from None

        try:
            response_data = response.json()

        except (requests.exceptions.JSONDecodeError, ValueError):
            raise OpenRouterClientError(
                "OpenRouter returned invalid JSON."
            ) from None

        if not isinstance(response_data, dict):
            raise OpenRouterClientError(
                "OpenRouter returned an invalid API response."
            )

        choices = response_data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise OpenRouterClientError(
                "OpenRouter response contains no choices."
            )

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise OpenRouterClientError(
                "OpenRouter response contains an invalid choice."
            )

        if first_choice.get("finish_reason") == "length":
            raise OpenRouterClientError(
                "OpenRouter response was truncated."
            )

        message = first_choice.get("message")
        if not isinstance(message, dict):
            raise OpenRouterClientError(
                "OpenRouter response contains no assistant message."
            )

        content = message.get("content")
        if not isinstance(content, str) or not content:
            raise OpenRouterClientError(
                "OpenRouter response contains no assistant text."
            )

        return content
