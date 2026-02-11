"""Unit tests for extraction provider factory."""

from unittest.mock import MagicMock, patch

import pytest

from app.pkgs.extraction.providers.factory import provide_provider
from app.pkgs.extraction.providers.groq_provider import GroqExtractionProvider
from app.pkgs.extraction.providers.openrouter_provider import (
    OpenRouterExtractionProvider,
)
from app.pkgs.extraction.providers.zai_provider import ZaiExtractionProvider


class TestProviderFactory:
    """Tests for provider selection and instantiation."""

    @patch("app.pkgs.extraction.providers.factory.settings")
    def test_provide_provider_openrouter(self, mock_settings: MagicMock):
        """Factory should return OpenRouter provider when configured."""
        mock_settings.EXTRACTION_PROVIDER = "openrouter"
        mock_settings.EXTRACTION_OCR_PROVIDER = ""
        mock_settings.EXTRACTION_STATEMENT_PROVIDER = ""
        mock_settings.OPENROUTER_API_KEY = "test-key"
        mock_settings.OPENROUTER_OCR_MODELS = "ocr-a,ocr-b"
        mock_settings.OPENROUTER_STATEMENT_MODELS = "stmt-a,stmt-b"

        provider = provide_provider()

        assert isinstance(provider, OpenRouterExtractionProvider)
        assert provider.name == "openrouter"
        assert len(provider.pipelines) == 2
        assert provider.pipelines[0].ocr_model == "ocr-a"
        assert provider.pipelines[0].statement_model == "stmt-a"

    @patch("app.pkgs.extraction.providers.factory.settings")
    def test_provide_provider_uses_default_models_when_empty(
        self, mock_settings: MagicMock
    ):
        """Empty model env vars should fall back to provider defaults."""
        mock_settings.EXTRACTION_PROVIDER = "openrouter"
        mock_settings.EXTRACTION_OCR_PROVIDER = ""
        mock_settings.EXTRACTION_STATEMENT_PROVIDER = ""
        mock_settings.OPENROUTER_API_KEY = "test-key"
        mock_settings.OPENROUTER_OCR_MODELS = ""
        mock_settings.OPENROUTER_STATEMENT_MODELS = ""

        provider = provide_provider()

        assert isinstance(provider, OpenRouterExtractionProvider)
        assert provider.ocr_models == OpenRouterExtractionProvider.DEFAULT_OCR_MODELS
        assert (
            provider.statement_models
            == OpenRouterExtractionProvider.DEFAULT_STATEMENT_MODELS
        )

    @patch("app.pkgs.extraction.providers.factory.ZaiExtractionProvider.create_client")
    @patch("app.pkgs.extraction.providers.factory.settings")
    def test_provide_provider_zai(
        self,
        mock_settings: MagicMock,
        mock_create_client: MagicMock,
    ):
        """Factory should return ZAI provider when configured."""
        mock_settings.EXTRACTION_PROVIDER = "zai"
        mock_settings.ZAI_API_KEY = "zai-key"
        mock_settings.ZAI_OCR_MODELS = "zai-ocr-a,zai-ocr-b"
        mock_settings.ZAI_STATEMENT_MODELS = "zai-stmt-a,zai-stmt-b"
        mock_settings.EXTRACTION_OCR_PROVIDER = ""
        mock_settings.EXTRACTION_STATEMENT_PROVIDER = ""
        mock_create_client.return_value = MagicMock()

        provider = provide_provider()

        assert isinstance(provider, ZaiExtractionProvider)
        assert provider.name == "zai"
        assert len(provider.pipelines) == 2
        assert provider.pipelines[0].ocr_model == "zai-ocr-a"
        assert provider.pipelines[0].statement_model == "zai-stmt-a"
        mock_create_client.assert_called_once_with("zai-key")

    @patch("app.pkgs.extraction.providers.factory.settings")
    @patch("app.pkgs.extraction.providers.factory.ZaiExtractionProvider.create_client")
    def test_mixed_providers_zai_ocr_openrouter_statement(
        self,
        mock_create_client: MagicMock,
        mock_settings: MagicMock,
    ):
        """Factory should compose different providers when split vars are set."""
        mock_settings.EXTRACTION_PROVIDER = "openrouter"
        mock_settings.EXTRACTION_OCR_PROVIDER = "zai"
        mock_settings.EXTRACTION_STATEMENT_PROVIDER = "openrouter"

        mock_settings.ZAI_API_KEY = "zai-key"
        mock_settings.ZAI_OCR_MODELS = "zai-ocr-a,zai-ocr-b"
        mock_settings.ZAI_STATEMENT_MODELS = "zai-stmt-a,zai-stmt-b"

        mock_settings.OPENROUTER_API_KEY = "or-key"
        mock_settings.OPENROUTER_OCR_MODELS = "or-ocr-a,or-ocr-b"
        mock_settings.OPENROUTER_STATEMENT_MODELS = "or-stmt-a,or-stmt-b"

        mock_create_client.return_value = MagicMock()

        provider = provide_provider()

        assert provider.name == "ocr=zai;statement=openrouter"
        assert len(provider.pipelines) == 2
        assert provider.pipelines[0].ocr_model == "zai-ocr-a"
        assert provider.pipelines[0].statement_model == "or-stmt-a"
        assert provider.pipelines[1].ocr_model == "zai-ocr-b"
        assert provider.pipelines[1].statement_model == "or-stmt-b"
        mock_create_client.assert_called_once_with("zai-key")

    @patch("app.pkgs.extraction.providers.factory.settings")
    def test_provide_provider_groq(self, mock_settings: MagicMock):
        """Factory should return Groq provider when configured."""
        mock_settings.EXTRACTION_PROVIDER = "groq"
        mock_settings.EXTRACTION_OCR_PROVIDER = ""
        mock_settings.EXTRACTION_STATEMENT_PROVIDER = ""
        mock_settings.GROQ_API_KEY = "groq-key"
        mock_settings.GROQ_OCR_MODELS = "groq-ocr-a,groq-ocr-b"
        mock_settings.GROQ_STATEMENT_MODELS = "groq-stmt-a,groq-stmt-b"

        provider = provide_provider()

        assert isinstance(provider, GroqExtractionProvider)
        assert provider.name == "groq"
        assert len(provider.pipelines) == 2
        assert provider.pipelines[0].ocr_model == "groq-ocr-a"
        assert provider.pipelines[0].statement_model == "groq-stmt-a"

    @patch("app.pkgs.extraction.providers.factory.settings")
    def test_provide_provider_groq_uses_default_models_when_empty(
        self, mock_settings: MagicMock
    ):
        """Empty model env vars should fall back to Groq provider defaults."""
        mock_settings.EXTRACTION_PROVIDER = "groq"
        mock_settings.EXTRACTION_OCR_PROVIDER = ""
        mock_settings.EXTRACTION_STATEMENT_PROVIDER = ""
        mock_settings.GROQ_API_KEY = "groq-key"
        mock_settings.GROQ_OCR_MODELS = ""
        mock_settings.GROQ_STATEMENT_MODELS = ""

        provider = provide_provider()

        assert isinstance(provider, GroqExtractionProvider)
        assert provider.ocr_models == GroqExtractionProvider.DEFAULT_OCR_MODELS
        assert (
            provider.statement_models == GroqExtractionProvider.DEFAULT_STATEMENT_MODELS
        )

    @patch("app.pkgs.extraction.providers.factory.settings")
    def test_unknown_provider_raises_error(self, mock_settings: MagicMock):
        """Unsupported provider names should fail fast."""
        mock_settings.EXTRACTION_PROVIDER = "unknown-provider"
        mock_settings.EXTRACTION_OCR_PROVIDER = ""
        mock_settings.EXTRACTION_STATEMENT_PROVIDER = ""
        mock_settings.OPENROUTER_API_KEY = "test-key"
        mock_settings.OPENROUTER_OCR_MODELS = ""
        mock_settings.OPENROUTER_STATEMENT_MODELS = ""

        with pytest.raises(ValueError, match="Unsupported extraction provider"):
            provide_provider()
