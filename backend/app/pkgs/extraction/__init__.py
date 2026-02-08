"""Extraction package for LLM-based PDF statement parsing.

Exports:
    OpenRouterClient: HTTP client for OpenRouter API
    ExtractionProvider: Provider protocol for pluggable backends
    CompositeExtractionProvider: Compose OCR and statement backends
    OpenRouterExtractionProvider: OpenRouter provider implementation
    ZaiExtractionProvider: ZAI provider implementation
    ExtractionService: High-level extraction orchestration
    ExtractionResult: Result wrapper with success/failure states
    ExtractedStatement: Parsed statement data model
    provide: Provider function for dependency injection
"""

from app.pkgs.extraction.client import OpenRouterClient
from app.pkgs.extraction.models import (
    ExtractedCard,
    ExtractedCycle,
    ExtractedStatement,
    ExtractedTransaction,
    ExtractionResult,
    InstallmentInfo,
    Money,
)
from app.pkgs.extraction.providers import (
    CompositeExtractionProvider,
    ExtractionProvider,
    OpenRouterExtractionProvider,
    ZaiExtractionProvider,
    provide_provider,
)
from app.pkgs.extraction.service import ExtractionService, provide

__all__ = [
    "OpenRouterClient",
    "CompositeExtractionProvider",
    "ExtractionProvider",
    "OpenRouterExtractionProvider",
    "ZaiExtractionProvider",
    "provide_provider",
    "ExtractionService",
    "ExtractionResult",
    "ExtractedStatement",
    "ExtractedTransaction",
    "ExtractedCycle",
    "ExtractedCard",
    "InstallmentInfo",
    "Money",
    "provide",
]
