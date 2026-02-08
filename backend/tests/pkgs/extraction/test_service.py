"""Unit tests for extraction service."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

from app.pkgs.extraction.prompt import EXTRACTION_PROMPT
from app.pkgs.extraction.providers.base import ExtractionPipeline
from app.pkgs.extraction.service import ExtractionService, provide


def _ocr_response_text(pages: list[dict[str, object]] | None = None) -> str:
    return json.dumps({"pages": pages or [{"page": 1, "text": "line 1\nline 2"}]})


def _valid_statement_json() -> str:
    return json.dumps(
        {
            "statement_id": "STMT-001",
            "period": {
                "start": "2025-01-01",
                "end": "2025-01-31",
                "due_date": "2025-02-10",
            },
            "current_balance": [{"amount": 100.00, "currency": "USD"}],
            "transactions": [
                {
                    "date": "2025-01-15",
                    "merchant": "Test Store",
                    "amount": {"amount": 50.00, "currency": "USD"},
                }
            ],
        }
    )


def _mock_provider() -> MagicMock:
    provider = MagicMock()
    provider.name = "mock"
    provider.pipelines = [
        ExtractionPipeline(ocr_model="ocr-primary", statement_model="stmt-primary"),
        ExtractionPipeline(ocr_model="ocr-fallback", statement_model="stmt-fallback"),
    ]
    provider.run_ocr = AsyncMock(return_value=_ocr_response_text())
    provider.run_statement = AsyncMock(return_value=_valid_statement_json())
    return provider


class TestExtractionService:
    """Tests for ExtractionService."""

    def test_init_creates_service_with_provider(self):
        """Test that ExtractionService initializes with provider."""
        provider = _mock_provider()
        service = ExtractionService(provider=provider)

        assert service.provider == provider

    def test_build_statement_prompt_includes_prompt_schema_and_ocr_text(self):
        """Test that statement prompt includes prompt, schema, and OCR text."""
        service = ExtractionService(provider=_mock_provider())

        prompt = service._build_statement_prompt(
            [{"page": 1, "text": "Amount 123.45 USD"}]
        )

        assert EXTRACTION_PROMPT in prompt
        assert "statement_id" in prompt
        assert "transactions" in prompt
        assert "OCR_TEXT (JSON with pages)" in prompt
        assert "Amount 123.45 USD" in prompt

    def test_extract_json_from_response_handles_raw_json(self):
        """Test that _extract_json_from_response() handles raw JSON."""
        service = ExtractionService(provider=_mock_provider())

        content = '{"statement_id": "123"}'
        result = service._extract_json_from_response(content)

        assert result == '{"statement_id": "123"}'

    def test_extract_json_from_response_handles_code_block(self):
        """Test that _extract_json_from_response() extracts JSON from code block."""
        service = ExtractionService(provider=_mock_provider())

        content = '```json\n{"statement_id": "123"}\n```'
        result = service._extract_json_from_response(content)

        assert result == '{"statement_id": "123"}'

    def test_extract_statement_uses_correct_model_pair_by_index(self):
        """Test that OCR and statement calls use the right model index pair."""
        provider = _mock_provider()
        service = ExtractionService(provider=provider)

        async def run_test():
            await service.extract_statement(b"test pdf", model_index=0)
            assert provider.run_ocr.call_args.kwargs["model"] == "ocr-primary"
            assert provider.run_statement.call_args.kwargs["model"] == "stmt-primary"

            await service.extract_statement(b"test pdf", model_index=1)
            assert provider.run_ocr.call_args.kwargs["model"] == "ocr-fallback"
            assert provider.run_statement.call_args.kwargs["model"] == "stmt-fallback"

        asyncio.run(run_test())

    def test_extract_statement_sends_ocr_text_to_statement_step(self):
        """Test that statement prompt includes OCR pages JSON wrapper."""
        provider = _mock_provider()
        provider.run_ocr = AsyncMock(
            return_value=_ocr_response_text([{"page": 2, "text": "PAGE TWO TEXT"}])
        )
        service = ExtractionService(provider=provider)

        async def run_test():
            await service.extract_statement(b"test pdf")
            prompt = provider.run_statement.call_args.kwargs["prompt"]

            assert "OCR_TEXT (JSON with pages)" in prompt
            assert '"page": 2' in prompt
            assert "PAGE TWO TEXT" in prompt
            assert "Now fill the schema using the OCR_TEXT above." in prompt

        asyncio.run(run_test())

    def test_extract_statement_parses_successful_response(self):
        """Test that extract_statement() parses successful response."""
        service = ExtractionService(provider=_mock_provider())

        async def run_test():
            result = await service.extract_statement(b"test pdf")

            assert result.success is True
            assert result.data is not None
            assert result.data.statement_id == "STMT-001"
            assert len(result.data.transactions) == 1
            assert result.data.transactions[0].merchant == "Test Store"
            assert result.error is None
            assert "provider=mock" in result.model_used
            assert "ocr=ocr-primary" in result.model_used
            assert "statement=stmt-primary" in result.model_used

        asyncio.run(run_test())

    def test_extract_statement_handles_validation_errors(self):
        """Test that extract_statement() handles validation errors with partial data."""
        provider = _mock_provider()
        # Missing required current_balance
        provider.run_statement = AsyncMock(
            return_value=json.dumps(
                {
                    "statement_id": "STMT-001",
                    "period": {
                        "start": "2025-01-01",
                        "end": "2025-01-31",
                        "due_date": "2025-02-10",
                    },
                    "transactions": [],
                }
            )
        )
        service = ExtractionService(provider=provider)

        async def run_test():
            result = await service.extract_statement(b"test pdf")

            assert result.success is False
            assert result.data is None
            assert result.partial_data is not None
            assert result.partial_data["statement_id"] == "STMT-001"
            assert result.error is not None
            assert "current_balance" in result.error
            assert "provider=mock" in result.model_used

        asyncio.run(run_test())

    def test_extract_statement_handles_provider_errors(self):
        """Test that extract_statement() handles provider errors."""
        provider = _mock_provider()
        provider.run_ocr = AsyncMock(side_effect=Exception("OCR API connection failed"))
        service = ExtractionService(provider=provider)

        async def run_test():
            result = await service.extract_statement(b"test pdf")

            assert result.success is False
            assert result.data is None
            assert result.error is not None
            assert "OCR API connection failed" in result.error
            assert "provider=mock" in result.model_used

        asyncio.run(run_test())

    def test_extract_statement_handles_invalid_ocr_pages(self):
        """Test that extract_statement() fails when OCR payload has no pages list."""
        provider = _mock_provider()
        provider.run_ocr = AsyncMock(return_value='{"not_pages": []}')
        service = ExtractionService(provider=provider)

        async def run_test():
            result = await service.extract_statement(b"test pdf")

            assert result.success is False
            assert result.error is not None
            assert "pages" in result.error

        asyncio.run(run_test())

    def test_extract_statement_handles_invalid_model_index(self):
        """Test that extract_statement() handles invalid model index."""
        service = ExtractionService(provider=_mock_provider())

        async def run_test():
            result = await service.extract_statement(b"test pdf", model_index=99)

            assert result.success is False
            assert result.error is not None
            assert "No more models" in result.error
            assert result.model_used == "none"

        asyncio.run(run_test())

    def test_extract_statement_handles_markdown_code_blocks(self):
        """Test that extract_statement() extracts JSON from markdown code blocks."""
        provider = _mock_provider()
        provider.run_statement = AsyncMock(
            return_value=f"```json\n{_valid_statement_json()}\n```"
        )
        service = ExtractionService(provider=provider)

        async def run_test():
            result = await service.extract_statement(b"test pdf")

            assert result.success is True
            assert result.data is not None
            assert result.data.statement_id == "STMT-001"

        asyncio.run(run_test())

    def test_extract_statement_logs_heartbeat_while_waiting_for_model(self):
        """Slow model calls should emit periodic heartbeat logs."""
        provider = _mock_provider()

        async def delayed_ocr(*args, **kwargs):
            del args, kwargs
            await asyncio.sleep(0.03)
            return _ocr_response_text()

        provider.run_ocr = AsyncMock(side_effect=delayed_ocr)
        service = ExtractionService(
            provider=provider,
            wait_log_interval_seconds=0.01,
        )

        async def run_test():
            with patch("app.pkgs.extraction.service.logger.info") as mock_info:
                result = await service.extract_statement(b"test pdf")
                assert result.success is True

                heartbeat_calls = [
                    call
                    for call in mock_info.call_args_list
                    if call.args
                    and isinstance(call.args[0], str)
                    and "Still waiting on model response" in call.args[0]
                ]
                assert heartbeat_calls

        asyncio.run(run_test())

    def test_extract_statement_disables_heartbeat_when_interval_non_positive(self):
        """Heartbeat logs should be disabled when interval is <= 0."""
        provider = _mock_provider()

        async def delayed_ocr(*args, **kwargs):
            del args, kwargs
            await asyncio.sleep(0.01)
            return _ocr_response_text()

        provider.run_ocr = AsyncMock(side_effect=delayed_ocr)
        service = ExtractionService(
            provider=provider,
            wait_log_interval_seconds=0,
        )

        async def run_test():
            with patch("app.pkgs.extraction.service.logger.info") as mock_info:
                result = await service.extract_statement(b"test pdf")
                assert result.success is True

                heartbeat_calls = [
                    call
                    for call in mock_info.call_args_list
                    if call.args
                    and isinstance(call.args[0], str)
                    and "Still waiting on model response" in call.args[0]
                ]
                assert not heartbeat_calls

        asyncio.run(run_test())


class TestProvideFunction:
    """Tests for the provide() function."""

    @patch("app.pkgs.extraction.service.provide_provider")
    def test_provide_returns_configured_service(self, mock_provide_provider: MagicMock):
        """Test that provide() wires service with provider from factory."""
        provider = _mock_provider()
        mock_provide_provider.return_value = provider

        service = provide()

        assert isinstance(service, ExtractionService)
        assert service.provider == provider
