"""Unit tests for extraction service."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

from app.pkgs.extraction.client import OpenRouterClient
from app.pkgs.extraction.prompt import EXTRACTION_PROMPT
from app.pkgs.extraction.service import ExtractionService, provide


class TestExtractionService:
    """Tests for ExtractionService."""

    def test_models_list_has_primary_and_fallback(self):
        """Test that MODELS list contains primary and fallback models."""
        assert len(ExtractionService.MODELS) >= 2
        assert "gemini-flash" in ExtractionService.MODELS[0]
        assert "gemini-pro" in ExtractionService.MODELS[1]

    def test_init_creates_service_with_client(self):
        """Test that ExtractionService initializes with client."""
        client = MagicMock(spec=OpenRouterClient)
        service = ExtractionService(client=client)

        assert service.client == client

    def test_build_prompt_includes_prompt_and_schema(self):
        """Test that _build_prompt() includes both prompt and schema."""
        client = MagicMock(spec=OpenRouterClient)
        service = ExtractionService(client=client)

        prompt = service._build_prompt()

        assert EXTRACTION_PROMPT in prompt
        assert "statement_id" in prompt
        assert "transactions" in prompt
        assert "credit_limit" in prompt
        assert "Límite de crédito" in prompt

    def test_extract_json_from_response_handles_raw_json(self):
        """Test that _extract_json_from_response() handles raw JSON."""
        client = MagicMock(spec=OpenRouterClient)
        service = ExtractionService(client=client)

        content = '{"statement_id": "123"}'
        result = service._extract_json_from_response(content)

        assert result == '{"statement_id": "123"}'

    def test_extract_json_from_response_handles_code_block(self):
        """Test that _extract_json_from_response() extracts JSON from code block."""
        client = MagicMock(spec=OpenRouterClient)
        service = ExtractionService(client=client)

        content = '```json\n{"statement_id": "123"}\n```'
        result = service._extract_json_from_response(content)

        assert result == '{"statement_id": "123"}'

    def test_extract_json_from_response_handles_code_block_no_lang(self):
        """Test that _extract_json_from_response() extracts from code block without language."""
        client = MagicMock(spec=OpenRouterClient)
        service = ExtractionService(client=client)

        content = '```\n{"statement_id": "456"}\n```'
        result = service._extract_json_from_response(content)

        assert result == '{"statement_id": "456"}'

    def test_extract_statement_uses_correct_model(self):
        """Test that extract_statement() uses correct model based on index."""
        client = MagicMock(spec=OpenRouterClient)
        client.complete_with_pdf = AsyncMock(
            return_value={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "statement_id": "STMT-001",
                                    "period": {
                                        "start": "2025-01-01",
                                        "end": "2025-01-31",
                                        "due_date": "2025-02-10",
                                    },
                                    "current_balance": [
                                        {"amount": 100.00, "currency": "USD"}
                                    ],
                                    "transactions": [],
                                }
                            )
                        }
                    }
                ]
            }
        )

        service = ExtractionService(client=client)
        pdf_bytes = b"test pdf"

        async def run_test():
            await service.extract_statement(pdf_bytes, model_index=0)
            call_kwargs = client.complete_with_pdf.call_args.kwargs
            assert call_kwargs["model"] == ExtractionService.MODELS[0]

            await service.extract_statement(pdf_bytes, model_index=1)
            call_kwargs = client.complete_with_pdf.call_args.kwargs
            assert call_kwargs["model"] == ExtractionService.MODELS[1]

        asyncio.run(run_test())

    def test_extract_statement_builds_correct_prompt(self):
        """Test that extract_statement() builds correct prompt."""
        client = MagicMock(spec=OpenRouterClient)
        client.complete_with_pdf = AsyncMock(
            return_value={
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "statement_id": "STMT-001",
                                    "period": {
                                        "start": "2025-01-01",
                                        "end": "2025-01-31",
                                        "due_date": "2025-02-10",
                                    },
                                    "current_balance": [
                                        {"amount": 100.00, "currency": "USD"}
                                    ],
                                    "transactions": [],
                                }
                            )
                        }
                    }
                ]
            }
        )

        service = ExtractionService(client=client)
        pdf_bytes = b"test pdf"

        async def run_test():
            await service.extract_statement(pdf_bytes)
            call_kwargs = client.complete_with_pdf.call_args.kwargs
            prompt = call_kwargs["prompt"]

            assert EXTRACTION_PROMPT in prompt
            assert "statement_id" in prompt  # From schema

        asyncio.run(run_test())

    def test_extract_statement_parses_successful_response(self):
        """Test that extract_statement() parses successful response."""
        client = MagicMock(spec=OpenRouterClient)
        response_data = {
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

        client.complete_with_pdf = AsyncMock(
            return_value={
                "choices": [{"message": {"content": json.dumps(response_data)}}]
            }
        )

        service = ExtractionService(client=client)

        async def run_test():
            result = await service.extract_statement(b"test pdf")

            assert result.success is True
            assert result.data is not None
            assert result.data.statement_id == "STMT-001"
            assert len(result.data.transactions) == 1
            assert result.data.transactions[0].merchant == "Test Store"
            assert result.error is None
            assert result.model_used == ExtractionService.MODELS[0]

        asyncio.run(run_test())

    def test_extract_statement_handles_validation_errors(self):
        """Test that extract_statement() handles validation errors with partial data."""
        client = MagicMock(spec=OpenRouterClient)
        # Missing required current_balance
        invalid_response = {
            "statement_id": "STMT-001",
            "period": {
                "start": "2025-01-01",
                "end": "2025-01-31",
                "due_date": "2025-02-10",
            },
            "transactions": [],
        }

        client.complete_with_pdf = AsyncMock(
            return_value={
                "choices": [{"message": {"content": json.dumps(invalid_response)}}]
            }
        )

        service = ExtractionService(client=client)

        async def run_test():
            result = await service.extract_statement(b"test pdf")

            assert result.success is False
            assert result.data is None
            assert result.partial_data is not None
            assert result.partial_data["statement_id"] == "STMT-001"
            assert result.error is not None
            assert "current_balance" in result.error
            assert result.model_used == ExtractionService.MODELS[0]

        asyncio.run(run_test())

    def test_extract_statement_handles_api_errors(self):
        """Test that extract_statement() handles API errors."""
        client = MagicMock(spec=OpenRouterClient)
        client.complete_with_pdf = AsyncMock(
            side_effect=Exception("API connection failed")
        )

        service = ExtractionService(client=client)

        async def run_test():
            result = await service.extract_statement(b"test pdf")

            assert result.success is False
            assert result.data is None
            assert result.error is not None
            assert "API connection failed" in result.error
            assert result.model_used == ExtractionService.MODELS[0]

        asyncio.run(run_test())

    def test_extract_statement_handles_empty_choices(self):
        """Test that extract_statement() handles empty choices in response."""
        client = MagicMock(spec=OpenRouterClient)
        client.complete_with_pdf = AsyncMock(return_value={"choices": []})

        service = ExtractionService(client=client)

        async def run_test():
            result = await service.extract_statement(b"test pdf")

            assert result.success is False
            assert result.error is not None
            assert "No choices" in result.error

        asyncio.run(run_test())

    def test_extract_statement_handles_invalid_model_index(self):
        """Test that extract_statement() handles invalid model index."""
        client = MagicMock(spec=OpenRouterClient)
        service = ExtractionService(client=client)

        async def run_test():
            result = await service.extract_statement(b"test pdf", model_index=99)

            assert result.success is False
            assert result.error is not None
            assert "No more models" in result.error
            assert result.model_used == "none"

        asyncio.run(run_test())

    def test_extract_statement_records_model_used(self):
        """Test that extract_statement() records model used in result."""
        client = MagicMock(spec=OpenRouterClient)
        response_data = {
            "statement_id": "STMT-001",
            "period": {
                "start": "2025-01-01",
                "end": "2025-01-31",
                "due_date": "2025-02-10",
            },
            "current_balance": [{"amount": 100.00, "currency": "USD"}],
            "transactions": [],
        }

        client.complete_with_pdf = AsyncMock(
            return_value={
                "choices": [{"message": {"content": json.dumps(response_data)}}]
            }
        )

        service = ExtractionService(client=client)

        async def run_test():
            result = await service.extract_statement(b"test pdf", model_index=1)
            assert result.model_used == ExtractionService.MODELS[1]

        asyncio.run(run_test())

    def test_extract_statement_handles_markdown_code_blocks(self):
        """Test that extract_statement() extracts JSON from markdown code blocks."""
        client = MagicMock(spec=OpenRouterClient)
        response_data = {
            "statement_id": "STMT-001",
            "period": {
                "start": "2025-01-01",
                "end": "2025-01-31",
                "due_date": "2025-02-10",
            },
            "current_balance": [{"amount": 100.00, "currency": "USD"}],
            "transactions": [],
        }
        markdown_content = f"```json\n{json.dumps(response_data)}\n```"

        client.complete_with_pdf = AsyncMock(
            return_value={"choices": [{"message": {"content": markdown_content}}]}
        )

        service = ExtractionService(client=client)

        async def run_test():
            result = await service.extract_statement(b"test pdf")

            assert result.success is True
            assert result.data is not None
            assert result.data.statement_id == "STMT-001"

        asyncio.run(run_test())


class TestProvideFunction:
    """Tests for the provide() function."""

    @patch("app.core.config.settings")
    def test_provide_returns_configured_service(self, mock_settings: MagicMock):
        """Test that provide() returns a configured ExtractionService."""
        mock_settings.OPENROUTER_API_KEY = "test-api-key"

        service = provide()

        assert isinstance(service, ExtractionService)
        assert isinstance(service.client, OpenRouterClient)
        assert service.client.api_key == "test-api-key"
        assert service.client.base_url == "https://openrouter.ai/api/v1"
