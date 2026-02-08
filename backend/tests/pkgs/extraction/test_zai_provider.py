"""Unit tests for ZAI extraction provider."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.pkgs.extraction.providers.zai_provider import ZaiExtractionProvider


def _ns(**kwargs):
    return SimpleNamespace(**kwargs)


class TestZaiExtractionProvider:
    """Tests for ZaiExtractionProvider."""

    def test_builds_pipelines_from_models(self):
        """Provider should create one pipeline per paired model index."""
        provider = ZaiExtractionProvider(
            client=MagicMock(),
            ocr_models=["ocr-a", "ocr-b", "ocr-c"],
            statement_models=["stmt-a", "stmt-b"],
        )

        assert len(provider.pipelines) == 2
        assert provider.pipelines[0].ocr_model == "ocr-a"
        assert provider.pipelines[0].statement_model == "stmt-a"
        assert provider.pipelines[1].ocr_model == "ocr-b"
        assert provider.pipelines[1].statement_model == "stmt-b"

    def test_create_client_uses_sdk_module(self):
        """create_client should load zai module and instantiate ZaiClient."""
        fake_client_cls = MagicMock()
        fake_module = _ns(ZaiClient=fake_client_cls)

        with patch(
            "app.pkgs.extraction.providers.zai_provider.importlib.import_module"
        ) as m:
            m.return_value = fake_module
            ZaiExtractionProvider.create_client("abc123")

        fake_client_cls.assert_called_once_with(api_key="abc123")

    def test_create_client_raises_when_sdk_missing(self):
        """Missing SDK should raise a clear runtime error."""
        with patch(
            "app.pkgs.extraction.providers.zai_provider.importlib.import_module"
        ) as m:
            m.side_effect = ImportError("No module named zai")
            with pytest.raises(RuntimeError, match="zai-sdk"):
                ZaiExtractionProvider.create_client("abc123")

    def test_layout_response_uses_layout_details(self):
        """OCR page extraction should prefer layout_details content when present."""
        provider = ZaiExtractionProvider(client=MagicMock())
        resp = _ns(
            layout_details=[
                [_ns(content="Page 1 line A"), _ns(content="Page 1 line B")],
                [_ns(content="Page 2 line A")],
            ],
            md_results=None,
            data_info=_ns(num_pages=2),
        )

        pages = provider._layout_response_to_pages(resp)
        assert pages == [
            {"page": 1, "text": "Page 1 line A\nPage 1 line B"},
            {"page": 2, "text": "Page 2 line A"},
        ]

    def test_layout_response_falls_back_to_md_results(self):
        """OCR page extraction should use md_results when details have no text."""
        provider = ZaiExtractionProvider(client=MagicMock())
        resp = _ns(
            layout_details=[[_ns(content="")]],
            md_results="Page 1 text\n---\nPage 2 text",
            data_info=_ns(num_pages=2),
        )

        pages = provider._layout_response_to_pages(resp)
        assert pages == [
            {"page": 1, "text": "Page 1 text"},
            {"page": 2, "text": "Page 2 text"},
        ]

    def test_layout_response_fallback_empty_pages(self):
        """OCR page extraction should produce empty pages if no content exists."""
        provider = ZaiExtractionProvider(client=MagicMock())
        resp = _ns(
            layout_details=None,
            md_results=None,
            data_info=_ns(num_pages=3),
        )

        pages = provider._layout_response_to_pages(resp)
        assert pages == [
            {"page": 1, "text": ""},
            {"page": 2, "text": ""},
            {"page": 3, "text": ""},
        ]

    def test_extract_first_json_object(self):
        """JSON extraction helper should pull first top-level object."""
        provider = ZaiExtractionProvider(client=MagicMock())
        extracted = provider._extract_first_json_object('prefix {"a":1} suffix')
        assert extracted == '{"a":1}'

    def test_run_statement_prefers_content(self):
        """Statement parsing should return message.content when present."""
        client = MagicMock()
        client.chat.completions.create.return_value = _ns(
            choices=[_ns(message=_ns(content='{"ok":true}', tool_calls=None))]
        )
        provider = ZaiExtractionProvider(client=client)

        async def run_test():
            result = await provider.run_statement(model="glm", prompt="prompt")
            assert result == '{"ok":true}'

        asyncio.run(run_test())

    def test_run_statement_falls_back_to_tool_call_arguments(self):
        """Statement parsing should use tool call arguments when content is empty."""
        client = MagicMock()
        client.chat.completions.create.return_value = _ns(
            choices=[
                _ns(
                    message=_ns(
                        content=None,
                        tool_calls=[_ns(function=_ns(arguments='{"tool":1}'))],
                        reasoning_content=None,
                    )
                )
            ]
        )
        provider = ZaiExtractionProvider(client=client)

        async def run_test():
            result = await provider.run_statement(model="glm", prompt="prompt")
            assert result == '{"tool":1}'

        asyncio.run(run_test())

    def test_run_statement_falls_back_to_reasoning_content_json(self):
        """Statement parsing should extract JSON from reasoning content as fallback."""
        client = MagicMock()
        client.chat.completions.create.return_value = _ns(
            choices=[
                _ns(
                    message=_ns(
                        content=None,
                        tool_calls=[],
                        reasoning_content='steps... {"r":2} ...done',
                    )
                )
            ]
        )
        provider = ZaiExtractionProvider(client=client)

        async def run_test():
            result = await provider.run_statement(model="glm", prompt="prompt")
            assert result == '{"r":2}'

        asyncio.run(run_test())

    def test_run_statement_raises_on_empty_content(self):
        """Statement parsing should fail fast if no content channel has JSON."""
        client = MagicMock()
        client.chat.completions.create.return_value = _ns(
            choices=[
                _ns(
                    message=_ns(
                        content=None, tool_calls=[], reasoning_content="no json"
                    )
                )
            ]
        )
        provider = ZaiExtractionProvider(client=client)

        async def run_test():
            with pytest.raises(ValueError, match="empty content"):
                await provider.run_statement(model="glm", prompt="prompt")

        asyncio.run(run_test())

    def test_run_ocr_returns_pages_json(self):
        """OCR should call layout_parsing and normalize pages into JSON text."""
        client = MagicMock()
        client.layout_parsing.create.return_value = _ns(
            layout_details=[[_ns(content="A")], [_ns(content="B")]],
            md_results=None,
            data_info=_ns(num_pages=2),
        )
        provider = ZaiExtractionProvider(client=client)

        async def run_test():
            text = await provider.run_ocr(
                model="glm-ocr", prompt="ignored", pdf_bytes=b"%PDF"
            )
            payload = json.loads(text)
            assert payload["pages"] == [
                {"page": 1, "text": "A"},
                {"page": 2, "text": "B"},
            ]

        asyncio.run(run_test())
