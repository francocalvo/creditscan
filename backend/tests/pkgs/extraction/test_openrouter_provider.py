"""Unit tests for OpenRouter extraction provider."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.pkgs.extraction.providers.openrouter_provider import (
    OpenRouterExtractionProvider,
)


def _openrouter_response(content: object) -> dict[str, object]:
    return {"choices": [{"message": {"content": content}}]}


class TestOpenRouterExtractionProvider:
    """Tests for OpenRouterExtractionProvider."""

    def test_builds_pipelines_from_models(self):
        """Provider should create one pipeline per paired model index."""
        client = MagicMock()
        provider = OpenRouterExtractionProvider(
            client=client,
            ocr_models=["ocr-a", "ocr-b", "ocr-c"],
            statement_models=["stmt-a", "stmt-b"],
        )

        assert len(provider.pipelines) == 2
        assert provider.pipelines[0].ocr_model == "ocr-a"
        assert provider.pipelines[0].statement_model == "stmt-a"
        assert provider.pipelines[1].ocr_model == "ocr-b"
        assert provider.pipelines[1].statement_model == "stmt-b"

    def test_extract_content_supports_string(self):
        """Content extraction should return raw string content."""
        client = MagicMock()
        provider = OpenRouterExtractionProvider(client=client)

        content = provider._extract_content(_openrouter_response('{"ok":true}'))
        assert content == '{"ok":true}'

    def test_extract_content_supports_array_parts(self):
        """Content extraction should support list part responses."""
        client = MagicMock()
        provider = OpenRouterExtractionProvider(client=client)

        content = provider._extract_content(
            _openrouter_response([{"text": "part-1"}, {"text": "part-2"}])
        )
        assert content == "part-1\npart-2"

    def test_extract_content_rejects_missing_choices(self):
        """Content extraction should fail on invalid payload shape."""
        client = MagicMock()
        provider = OpenRouterExtractionProvider(client=client)

        with pytest.raises(ValueError, match="No choices"):
            provider._extract_content({"choices": []})

    def test_run_ocr_uses_complete_with_pdf(self):
        """OCR call should delegate to complete_with_pdf."""
        client = MagicMock()
        client.complete_with_pdf = AsyncMock(
            return_value=_openrouter_response('{"pages":[{"page":1,"text":"abc"}]}')
        )
        provider = OpenRouterExtractionProvider(client=client)

        async def run_test():
            content = await provider.run_ocr(
                model="ocr-model",
                prompt="ocr prompt",
                pdf_bytes=b"%PDF-1.4",
            )

            assert '"pages"' in content
            call_kwargs = client.complete_with_pdf.call_args.kwargs
            assert call_kwargs["model"] == "ocr-model"
            assert call_kwargs["prompt"] == "ocr prompt"
            assert call_kwargs["pdf_bytes"] == b"%PDF-1.4"
            assert call_kwargs["response_format"] == {"type": "json_object"}

        asyncio.run(run_test())

    def test_run_statement_uses_complete_with_text(self):
        """Statement call should delegate to complete_with_text."""
        client = MagicMock()
        client.complete_with_text = AsyncMock(
            return_value=_openrouter_response('{"statement_id":"x"}')
        )
        provider = OpenRouterExtractionProvider(client=client)

        async def run_test():
            content = await provider.run_statement(
                model="stmt-model",
                prompt="statement prompt",
            )

            assert '"statement_id"' in content
            call_kwargs = client.complete_with_text.call_args.kwargs
            assert call_kwargs["model"] == "stmt-model"
            assert call_kwargs["prompt"] == "statement prompt"
            assert call_kwargs["response_format"] == {"type": "json_object"}

        asyncio.run(run_test())
