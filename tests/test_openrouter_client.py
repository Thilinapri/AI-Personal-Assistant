import os
import unittest
from unittest.mock import MagicMock, patch

import requests

from src.ai.openrouter_client import (
    OpenRouterClient,
    OpenRouterClientError,
)


class OpenRouterClientTests(unittest.TestCase):

    def setUp(self):
        self.dotenv_patcher = patch(
            "src.ai.openrouter_client.load_dotenv"
        )
        self.dotenv_patcher.start()
        self.session = MagicMock()
        self.response = MagicMock()
        self.response.status_code = 200
        self.response.json.return_value = {
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": '{"memories": []}'
                    },
                }
            ]
        }
        self.session.post.return_value = self.response
        self.client = OpenRouterClient(
            api_key="fake-test-key",
            model="google/test-model",
            session=self.session,
        )

    def tearDown(self):
        self.dotenv_patcher.stop()

    def test_request_format(self):
        result = self.client.generate_text(
            "Prepared synthetic prompt"
        )

        self.assertEqual(
            result,
            '{"memories": []}',
        )
        self.session.post.assert_called_once()

        args, kwargs = self.session.post.call_args
        self.assertEqual(
            args[0],
            "https://openrouter.ai/api/v1/chat/completions",
        )
        self.assertEqual(
            kwargs["headers"]["Authorization"],
            "Bearer fake-test-key",
        )
        self.assertEqual(
            kwargs["json"]["model"],
            "google/test-model",
        )
        self.assertEqual(
            kwargs["json"]["messages"],
            [
                {
                    "role": "user",
                    "content": "Prepared synthetic prompt",
                }
            ],
        )
        self.assertEqual(
            kwargs["json"]["temperature"],
            0.2,
        )
        self.assertEqual(
            kwargs["json"]["response_format"],
            {"type": "json_object"},
        )
        self.assertEqual(
            kwargs["json"]["provider"]["data_collection"],
            "deny",
        )
        self.assertTrue(
            kwargs["json"]["provider"]["require_parameters"]
        )

    def test_injected_fake_key_and_session(self):
        self.client.generate_text("test prompt")
        self.assertEqual(
            self.session.post.call_args.kwargs[
                "headers"
            ]["Authorization"],
            "Bearer fake-test-key",
        )
        self.assertIs(
            self.client.session,
            self.session,
        )

    def test_missing_api_key_is_rejected(self):
        with patch.dict(
            os.environ,
            {"OPENROUTER_API_KEY": ""},
            clear=False,
        ):
            with self.assertRaises(
                OpenRouterClientError
            ):
                OpenRouterClient(
                    session=MagicMock()
                )

    def test_empty_and_whitespace_prompts_make_no_request(
        self,
    ):
        for prompt in ("", "   ", "\n\t"):
            with self.subTest(prompt=prompt):
                with self.assertRaises(
                    OpenRouterClientError
                ):
                    self.client.generate_text(prompt)

        self.session.post.assert_not_called()

    def test_successful_response_returns_content_unchanged(
        self,
    ):
        original_content = (
            '{"memories": [{"title": "Test"}]}'
        )
        self.response.json.return_value = {
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": original_content
                    },
                }
            ]
        }

        result = self.client.generate_text(
            "test prompt"
        )

        self.assertEqual(
            result,
            original_content,
        )

    def test_http_error_is_safe(self):
        self.response.status_code = 401
        self.response.raise_for_status.side_effect = (
            requests.HTTPError(
                "raw secret fake-test-key private prompt"
            )
        )

        with self.assertRaises(
            OpenRouterClientError
        ) as raised:
            self.client.generate_text("private prompt")

        message = str(raised.exception)
        self.assertIn("401", message)
        self.assertNotIn("fake-test-key", message)
        self.assertNotIn("private prompt", message)
        self.assertNotIn("raw secret", message)

    def test_timeout_is_safe(self):
        self.session.post.side_effect = requests.Timeout(
            "timeout fake-test-key private prompt"
        )

        with self.assertRaises(
            OpenRouterClientError
        ) as raised:
            self.client.generate_text("private prompt")

        self.assertEqual(
            str(raised.exception),
            "OpenRouter request timed out.",
        )

    def test_other_requests_exception_is_safe(self):
        self.session.post.side_effect = requests.RequestException(
            "fake-test-key private prompt raw body"
        )

        with self.assertRaises(
            OpenRouterClientError
        ) as raised:
            self.client.generate_text("private prompt")

        message = str(raised.exception)
        self.assertEqual(
            message,
            "OpenRouter request failed.",
        )
        self.assertNotIn("fake-test-key", message)
        self.assertNotIn("private prompt", message)
        self.assertNotIn("raw body", message)

    def test_invalid_json_response_is_rejected(self):
        self.response.json.side_effect = ValueError(
            "raw private response body"
        )

        with self.assertRaises(
            OpenRouterClientError
        ) as raised:
            self.client.generate_text("private prompt")

        message = str(raised.exception)
        self.assertEqual(
            message,
            "OpenRouter returned invalid JSON.",
        )
        self.assertNotIn("fake-test-key", message)
        self.assertNotIn("private prompt", message)
        self.assertNotIn("raw private", message)

    def test_missing_or_invalid_choices_are_rejected(self):
        cases = (
            {},
            {"choices": None},
            {"choices": []},
            {"choices": [None]},
        )

        for payload in cases:
            with self.subTest(payload=payload):
                self.response.json.side_effect = None
                self.response.json.return_value = payload

                with self.assertRaises(
                    OpenRouterClientError
                ):
                    self.client.generate_text(
                        "private prompt"
                    )

    def test_missing_invalid_message_is_rejected(self):
        cases = (
            {"choices": [{}]},
            {"choices": [{"message": None}]},
        )

        for payload in cases:
            with self.subTest(payload=payload):
                self.response.json.side_effect = None
                self.response.json.return_value = payload

                with self.assertRaises(
                    OpenRouterClientError
                ):
                    self.client.generate_text(
                        "private prompt"
                    )

    def test_missing_or_invalid_content_is_rejected(self):
        cases = (
            {"choices": [{"message": {"content": ""}}]},
            {"choices": [{"message": {"content": None}}]},
            {"choices": [{"message": {"content": 123}}]},
        )

        for payload in cases:
            with self.subTest(payload=payload):
                self.response.json.side_effect = None
                self.response.json.return_value = payload

                with self.assertRaises(
                    OpenRouterClientError
                ):
                    self.client.generate_text(
                        "private prompt"
                    )

    def test_truncated_response_is_rejected(self):
        self.response.json.return_value = {
            "choices": [
                {
                    "finish_reason": "length",
                    "message": {
                        "content": "partial response"
                    },
                }
            ]
        }

        with self.assertRaisesRegex(
            OpenRouterClientError,
            "truncated",
        ):
            self.client.generate_text(
                "private prompt"
            )

    def test_exceptions_do_not_expose_sensitive_values(self):
        self.response.status_code = 500
        self.response.raise_for_status.side_effect = (
            requests.HTTPError(
                "fake-test-key private prompt raw-response-body"
            )
        )

        with self.assertRaises(
            OpenRouterClientError
        ) as raised:
            self.client.generate_text("private prompt")

        message = str(raised.exception)
        self.assertNotIn("fake-test-key", message)
        self.assertNotIn("private prompt", message)
        self.assertNotIn("raw-response-body", message)


if __name__ == "__main__":
    unittest.main()
