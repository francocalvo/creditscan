"""Unit tests for Groq client."""

import asyncio
import base64
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.pkgs.extraction.groq_client import GroqClient


class TestGroqClient:
    """Tests for GroqClient."""

    def test_init_sets_api_key_and_base_url(self):
        """Test that GroqClient initializes with API key."""
        client = GroqClient(api_key="test-key")

        assert client.api_key == "test-key"
        assert client.base_url == "https://api.groq.com/openai/v1"

    def test_init_with_custom_base_url(self):
        """Test that GroqClient accepts custom base URL."""
        client = GroqClient(
            api_key="test-key",
            base_url="https://custom.api.com/v1",
        )

        assert client.api_key == "test-key"
        assert client.base_url == "https://custom.api.com/v1"

    def test_complete_with_pdf_encodes_pdf_correctly(self):
        """Test that complete_with_pdf() encodes PDF as base64."""
        client = GroqClient(api_key="test-key")
        pdf_bytes = b"test pdf content"
        expected_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "{}"}}]}
        mock_response.raise_for_status = MagicMock()

        async def run_test():
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                mock_client.post.return_value = mock_response
                mock_client_class.return_value = mock_client

                await client.complete_with_pdf(
                    model="test-model",
                    prompt="test prompt",
                    pdf_bytes=pdf_bytes,
                )

                call_args = mock_client.post.call_args
                payload = call_args.kwargs["json"]
                content = payload["messages"][0]["content"]
                image_url = content[1]["image_url"]["url"]

                assert f"data:application/pdf;base64,{expected_base64}" == image_url

        asyncio.run(run_test())

    def test_complete_with_pdf_sends_correct_request_format(self):
        """Test that complete_with_pdf() sends correct request format."""
        client = GroqClient(api_key="test-key")
        pdf_bytes = b"test pdf"

        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "{}"}}]}
        mock_response.raise_for_status = MagicMock()

        async def run_test():
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                mock_client.post.return_value = mock_response
                mock_client_class.return_value = mock_client

                await client.complete_with_pdf(
                    model="llama-4-maverick",
                    prompt="Extract data",
                    pdf_bytes=pdf_bytes,
                )

                call_args = mock_client.post.call_args
                url = call_args.args[0]
                payload = call_args.kwargs["json"]

                assert url == "https://api.groq.com/openai/v1/chat/completions"
                assert payload["model"] == "llama-4-maverick"
                assert payload["messages"][0]["role"] == "user"
                assert payload["messages"][0]["content"][0]["type"] == "text"
                assert payload["messages"][0]["content"][0]["text"] == "Extract data"
                assert payload["messages"][0]["content"][1]["type"] == "image_url"

        asyncio.run(run_test())

    def test_complete_with_pdf_includes_auth_header(self):
        """Test that complete_with_pdf() includes Authorization header."""
        client = GroqClient(api_key="gsk-test-123")
        pdf_bytes = b"test pdf"

        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "{}"}}]}
        mock_response.raise_for_status = MagicMock()

        async def run_test():
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                mock_client.post.return_value = mock_response
                mock_client_class.return_value = mock_client

                await client.complete_with_pdf(
                    model="test-model",
                    prompt="test prompt",
                    pdf_bytes=pdf_bytes,
                )

                call_args = mock_client.post.call_args
                headers = call_args.kwargs["headers"]

                assert headers["Authorization"] == "Bearer gsk-test-123"
                assert headers["Content-Type"] == "application/json"

        asyncio.run(run_test())

    def test_complete_with_pdf_returns_parsed_response(self):
        """Test that complete_with_pdf() returns parsed JSON response."""
        client = GroqClient(api_key="test-key")
        pdf_bytes = b"test pdf"

        expected_response = {
            "id": "gen-123",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": '{"statement_id": "123"}',
                    }
                }
            ],
        }

        mock_response = MagicMock()
        mock_response.json.return_value = expected_response

        async def run_test():
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                mock_client.post.return_value = mock_response
                mock_client_class.return_value = mock_client

                result = await client.complete_with_pdf(
                    model="test-model",
                    prompt="test prompt",
                    pdf_bytes=pdf_bytes,
                )

                assert result == expected_response
                assert (
                    result["choices"][0]["message"]["content"]
                    == '{"statement_id": "123"}'
                )

        asyncio.run(run_test())

    def test_complete_with_pdf_handles_timeout(self):
        """Test that complete_with_pdf() raises TimeoutException on timeout."""
        client = GroqClient(api_key="test-key")
        pdf_bytes = b"test pdf"

        async def run_test():
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                mock_client.post.side_effect = httpx.TimeoutException(
                    "Connection timed out"
                )
                mock_client_class.return_value = mock_client

                with pytest.raises(httpx.TimeoutException):
                    await client.complete_with_pdf(
                        model="test-model",
                        prompt="test prompt",
                        pdf_bytes=pdf_bytes,
                        timeout=30.0,
                    )

        asyncio.run(run_test())

    def test_complete_with_pdf_handles_http_errors(self):
        """Test that complete_with_pdf() raises HTTPStatusError on API error."""
        client = GroqClient(api_key="test-key")
        pdf_bytes = b"test pdf"

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate limit exceeded",
            request=httpx.Request(
                "POST", "https://api.groq.com/openai/v1/chat/completions"
            ),
            response=httpx.Response(429),
        )

        async def run_test():
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                mock_client.post.return_value = mock_response
                mock_client_class.return_value = mock_client

                with pytest.raises(httpx.HTTPStatusError):
                    await client.complete_with_pdf(
                        model="test-model",
                        prompt="test prompt",
                        pdf_bytes=pdf_bytes,
                    )

        asyncio.run(run_test())

    def test_complete_with_text_sends_correct_request_format(self):
        """Test that complete_with_text() sends text-only request format."""
        client = GroqClient(api_key="test-key")

        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "{}"}}]}

        async def run_test():
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                mock_client.post.return_value = mock_response
                mock_client_class.return_value = mock_client

                await client.complete_with_text(
                    model="gpt-oss-120b",
                    prompt="OCR_TEXT...",
                )

                call_args = mock_client.post.call_args
                url = call_args.args[0]
                payload = call_args.kwargs["json"]

                assert url == "https://api.groq.com/openai/v1/chat/completions"
                assert payload["model"] == "gpt-oss-120b"
                assert payload["messages"][0]["role"] == "user"
                assert payload["messages"][0]["content"] == "OCR_TEXT..."

        asyncio.run(run_test())

    def test_complete_with_pdf_supports_response_format(self):
        """Test that complete_with_pdf() forwards response_format when provided."""
        client = GroqClient(api_key="test-key")
        pdf_bytes = b"test pdf"

        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "{}"}}]}

        async def run_test():
            with patch("httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                mock_client.post.return_value = mock_response
                mock_client_class.return_value = mock_client

                await client.complete_with_pdf(
                    model="test-model",
                    prompt="test prompt",
                    pdf_bytes=pdf_bytes,
                    response_format={"type": "json_object"},
                )

                call_args = mock_client.post.call_args
                payload = call_args.kwargs["json"]
                assert payload["response_format"] == {"type": "json_object"}

        asyncio.run(run_test())
