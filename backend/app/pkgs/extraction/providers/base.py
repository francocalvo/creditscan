"""Provider abstractions for OCR + statement extraction pipelines."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ExtractionPipeline:
    """Model pair used for one OCR->statement extraction attempt."""

    ocr_model: str
    statement_model: str


class ExtractionProvider(Protocol):
    """Provider contract for extraction backends."""

    name: str
    pipelines: list[ExtractionPipeline]
    ocr_models: list[str]
    statement_models: list[str]

    async def run_ocr(
        self,
        *,
        model: str,
        prompt: str,
        pdf_bytes: bytes,
    ) -> str:
        """Run OCR over a PDF and return raw textual model content."""
        ...

    async def run_statement(
        self,
        *,
        model: str,
        prompt: str,
    ) -> str:
        """Generate statement JSON content from OCR text prompt."""
        ...
