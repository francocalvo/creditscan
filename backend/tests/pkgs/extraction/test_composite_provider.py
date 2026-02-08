"""Unit tests for composite extraction provider."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.pkgs.extraction.providers.base import ExtractionPipeline
from app.pkgs.extraction.providers.composite_provider import CompositeExtractionProvider


def _mock_provider(name: str, ocr_models: list[str], statement_models: list[str]):
    provider = MagicMock()
    provider.name = name
    provider.ocr_models = ocr_models
    provider.statement_models = statement_models
    provider.pipelines = [
        ExtractionPipeline(
            ocr_model=ocr_models[0] if ocr_models else "ocr-none",
            statement_model=statement_models[0] if statement_models else "stmt-none",
        )
    ]
    provider.run_ocr = AsyncMock(return_value='{"pages":[{"page":1,"text":"abc"}]}')
    provider.run_statement = AsyncMock(return_value='{"statement_id":"x"}')
    return provider


class TestCompositeExtractionProvider:
    """Tests for provider composition behavior."""

    def test_builds_pipelines_from_independent_model_lists(self):
        """Pipelines should pair OCR and statement models by index."""
        ocr_provider = _mock_provider(
            name="ocr-p",
            ocr_models=["ocr-a", "ocr-b"],
            statement_models=["unused-1"],
        )
        statement_provider = _mock_provider(
            name="stmt-p",
            ocr_models=["unused-2"],
            statement_models=["stmt-a", "stmt-b", "stmt-c"],
        )

        provider = CompositeExtractionProvider(
            ocr_provider=ocr_provider,
            statement_provider=statement_provider,
        )

        assert provider.name == "ocr=ocr-p;statement=stmt-p"
        assert len(provider.pipelines) == 2
        assert provider.pipelines[0].ocr_model == "ocr-a"
        assert provider.pipelines[0].statement_model == "stmt-a"
        assert provider.pipelines[1].ocr_model == "ocr-b"
        assert provider.pipelines[1].statement_model == "stmt-b"

    def test_delegates_ocr_and_statement_calls(self):
        """Composite should delegate calls to respective providers."""
        ocr_provider = _mock_provider(
            name="ocr-p",
            ocr_models=["ocr-a"],
            statement_models=["unused"],
        )
        statement_provider = _mock_provider(
            name="stmt-p",
            ocr_models=["unused"],
            statement_models=["stmt-a"],
        )
        provider = CompositeExtractionProvider(
            ocr_provider=ocr_provider,
            statement_provider=statement_provider,
        )

        async def run_test():
            ocr_content = await provider.run_ocr(
                model="ocr-a",
                prompt="ocr prompt",
                pdf_bytes=b"%PDF",
            )
            statement_content = await provider.run_statement(
                model="stmt-a",
                prompt="statement prompt",
            )

            assert '"pages"' in ocr_content
            assert '"statement_id"' in statement_content
            ocr_provider.run_ocr.assert_called_once_with(
                model="ocr-a",
                prompt="ocr prompt",
                pdf_bytes=b"%PDF",
            )
            statement_provider.run_statement.assert_called_once_with(
                model="stmt-a",
                prompt="statement prompt",
            )

        asyncio.run(run_test())
