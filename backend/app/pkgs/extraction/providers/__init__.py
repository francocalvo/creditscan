"""Extraction provider abstractions and implementations."""

from app.pkgs.extraction.providers.base import ExtractionPipeline, ExtractionProvider
from app.pkgs.extraction.providers.composite_provider import CompositeExtractionProvider
from app.pkgs.extraction.providers.factory import provide_provider
from app.pkgs.extraction.providers.openrouter_provider import (
    OpenRouterExtractionProvider,
)
from app.pkgs.extraction.providers.zai_provider import ZaiExtractionProvider

__all__ = [
    "ExtractionPipeline",
    "ExtractionProvider",
    "CompositeExtractionProvider",
    "OpenRouterExtractionProvider",
    "ZaiExtractionProvider",
    "provide_provider",
]
