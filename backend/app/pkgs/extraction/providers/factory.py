"""Factory and registry for extraction providers."""

from app.core.config import settings
from app.pkgs.extraction.client import OpenRouterClient
from app.pkgs.extraction.groq_client import GroqClient
from app.pkgs.extraction.providers.base import ExtractionProvider
from app.pkgs.extraction.providers.composite_provider import CompositeExtractionProvider
from app.pkgs.extraction.providers.groq_provider import GroqExtractionProvider
from app.pkgs.extraction.providers.openrouter_provider import (
    OpenRouterExtractionProvider,
)
from app.pkgs.extraction.providers.zai_provider import ZaiExtractionProvider


def _parse_models(raw: str, fallback: list[str]) -> list[str]:
    models = [item.strip() for item in raw.split(",") if item.strip()]
    return models or fallback


def _build_provider(provider_name: str) -> ExtractionProvider:
    normalized = provider_name.strip().lower()

    if normalized == "openrouter":
        client = OpenRouterClient(api_key=settings.OPENROUTER_API_KEY)
        ocr_models = _parse_models(
            settings.OPENROUTER_OCR_MODELS,
            OpenRouterExtractionProvider.DEFAULT_OCR_MODELS,
        )
        statement_models = _parse_models(
            settings.OPENROUTER_STATEMENT_MODELS,
            OpenRouterExtractionProvider.DEFAULT_STATEMENT_MODELS,
        )
        return OpenRouterExtractionProvider(
            client=client,
            ocr_models=ocr_models,
            statement_models=statement_models,
        )

    if normalized == "zai":
        client = ZaiExtractionProvider.create_client(settings.ZAI_API_KEY)
        ocr_models = _parse_models(
            settings.ZAI_OCR_MODELS,
            ZaiExtractionProvider.DEFAULT_OCR_MODELS,
        )
        statement_models = _parse_models(
            settings.ZAI_STATEMENT_MODELS,
            ZaiExtractionProvider.DEFAULT_STATEMENT_MODELS,
        )
        return ZaiExtractionProvider(
            client=client,
            ocr_models=ocr_models,
            statement_models=statement_models,
        )

    if normalized == "groq":
        client = GroqClient(api_key=settings.GROQ_API_KEY)
        ocr_models = _parse_models(
            settings.GROQ_OCR_MODELS,
            GroqExtractionProvider.DEFAULT_OCR_MODELS,
        )
        statement_models = _parse_models(
            settings.GROQ_STATEMENT_MODELS,
            GroqExtractionProvider.DEFAULT_STATEMENT_MODELS,
        )
        return GroqExtractionProvider(
            client=client,
            ocr_models=ocr_models,
            statement_models=statement_models,
        )

    raise ValueError(
        f"Unsupported extraction provider '{provider_name}'. "
        "Supported providers: openrouter, zai, groq"
    )


def provide_provider() -> ExtractionProvider:
    """Instantiate extraction provider from runtime settings."""
    default_provider = settings.EXTRACTION_PROVIDER.strip().lower()
    ocr_provider_name = (
        settings.EXTRACTION_OCR_PROVIDER.strip().lower() or default_provider
    )
    statement_provider_name = (
        settings.EXTRACTION_STATEMENT_PROVIDER.strip().lower() or default_provider
    )

    if ocr_provider_name == statement_provider_name:
        return _build_provider(ocr_provider_name)

    return CompositeExtractionProvider(
        ocr_provider=_build_provider(ocr_provider_name),
        statement_provider=_build_provider(statement_provider_name),
    )
