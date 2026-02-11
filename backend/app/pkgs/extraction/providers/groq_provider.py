"""Groq-backed extraction provider."""

import logging
from typing import Any, cast

from app.pkgs.extraction.groq_client import GroqClient
from app.pkgs.extraction.providers.base import ExtractionPipeline

logger = logging.getLogger(__name__)


class GroqExtractionProvider:
    """Extraction provider implementation using Groq chat completions."""

    name = "groq"

    DEFAULT_OCR_MODELS = [
        "meta-llama/llama-4-maverick-17b-128e-instruct",  # Primary OCR
        "meta-llama/llama-4-maverick-17b-128e-instruct",  # Fallback OCR
    ]
    DEFAULT_STATEMENT_MODELS = [
        "openai/gpt-oss-120b",  # Primary statement parser
        "openai/gpt-oss-120b",  # Fallback statement parser
    ]

    def __init__(
        self,
        client: GroqClient,
        *,
        ocr_models: list[str] | None = None,
        statement_models: list[str] | None = None,
    ) -> None:
        self.client = client
        self.ocr_models = ocr_models or self.DEFAULT_OCR_MODELS.copy()
        self.statement_models = statement_models or self.DEFAULT_STATEMENT_MODELS.copy()
        self.pipelines = self._build_pipelines()

    def _build_pipelines(self) -> list[ExtractionPipeline]:
        count = min(len(self.ocr_models), len(self.statement_models))
        pipelines = [
            ExtractionPipeline(
                ocr_model=self.ocr_models[idx],
                statement_model=self.statement_models[idx],
            )
            for idx in range(count)
        ]
        if not pipelines:
            raise ValueError("Groq provider has no OCR->statement model pipelines")
        return pipelines

    def _extract_content(self, response: dict[str, object]) -> str:
        """Extract string content from Groq response payload."""
        choices_raw = response.get("choices", [])
        if not isinstance(choices_raw, list) or not choices_raw:
            raise ValueError("No choices in API response")

        first_choice = cast(Any, choices_raw[0])
        if not isinstance(first_choice, dict):
            raise ValueError("Invalid choice format in response")

        first_choice_dict = cast(dict[str, Any], first_choice)
        message = first_choice_dict.get("message", {})
        if not isinstance(message, dict):
            raise ValueError("Invalid message format in response")

        message_dict = cast(dict[str, Any], message)
        content = message_dict.get("content", "")
        if isinstance(content, str):
            return content

        # Some providers return content as an array of parts.
        if isinstance(content, list):
            text_parts: list[str] = []
            content_parts = cast(list[object], content)
            for part_raw in content_parts:
                if isinstance(part_raw, dict):
                    part = cast(dict[str, object], part_raw)
                    text_value = part.get("text")
                    if isinstance(text_value, str):
                        text_parts.append(text_value)
            if text_parts:
                return "\n".join(text_parts)

        raise ValueError("Invalid content format in response")

    async def run_ocr(
        self,
        *,
        model: str,
        prompt: str,
        pdf_bytes: bytes,
    ) -> str:
        """Run OCR model on a PDF and return model content."""
        logger.info(f"Groq OCR call using model: {model}")
        response = await self.client.complete_with_pdf(
            model=model,
            prompt=prompt,
            pdf_bytes=pdf_bytes,
            response_format={"type": "json_object"},
        )
        return self._extract_content(response)

    async def run_statement(
        self,
        *,
        model: str,
        prompt: str,
    ) -> str:
        """Run statement model on OCR text and return model content."""
        logger.info(f"Groq statement call using model: {model}")
        response = await self.client.complete_with_text(
            model=model,
            prompt=prompt,
            response_format={"type": "json_object"},
        )
        return self._extract_content(response)
