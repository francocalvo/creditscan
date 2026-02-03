"""High-level extraction service for PDF statement parsing."""

import json
import logging
import re
from typing import Any, cast

from pydantic import ValidationError

from app.pkgs.extraction.client import OpenRouterClient
from app.pkgs.extraction.models import ExtractedStatement, ExtractionResult
from app.pkgs.extraction.prompt import EXTRACTION_PROMPT, EXTRACTION_SCHEMA

logger = logging.getLogger(__name__)


class ExtractionService:
    """Service for extracting statement data from PDF files using LLMs."""

    MODELS = [
        "google/gemini-flash-1.5",  # Primary (fast)
        "google/gemini-pro-1.5",  # Fallback (more capable)
    ]

    def __init__(self, client: OpenRouterClient) -> None:
        """Initialize extraction service.

        Args:
            client: OpenRouter API client
        """
        self.client = client

    def _build_prompt(self) -> str:
        """Build the full extraction prompt with schema.

        Returns:
            Complete prompt string with schema appended
        """
        schema_str = json.dumps(EXTRACTION_SCHEMA, indent=2)
        return f"{EXTRACTION_PROMPT}\n{schema_str}"

    def _extract_json_from_response(self, content: str) -> str:
        """Extract JSON from response content, handling markdown code blocks.

        Args:
            content: Raw response content from LLM

        Returns:
            Extracted JSON string
        """
        # Try to extract JSON from markdown code block
        code_block_pattern = r"```(?:json)?\s*([\s\S]*?)```"
        match = re.search(code_block_pattern, content)
        if match:
            return match.group(1).strip()
        # Otherwise return content as-is (might be raw JSON)
        return content.strip()

    async def extract_statement(
        self,
        pdf_bytes: bytes,
        model_index: int = 0,
    ) -> ExtractionResult:
        """Extract statement data from PDF.

        Args:
            pdf_bytes: PDF file contents
            model_index: Index into MODELS list (0 = primary, 1 = fallback)

        Returns:
            ExtractionResult with success/failure state and data
        """
        if model_index >= len(self.MODELS):
            return ExtractionResult(
                success=False,
                error="No more models available for extraction",
                model_used="none",
            )

        model = self.MODELS[model_index]
        prompt = self._build_prompt()

        try:
            logger.info(f"Starting extraction with model: {model}")
            response = await self.client.complete_with_pdf(
                model=model,
                prompt=prompt,
                pdf_bytes=pdf_bytes,
            )

            # Extract content from response
            choices_raw = response.get("choices", [])
            if not isinstance(choices_raw, list) or not choices_raw:
                return ExtractionResult(
                    success=False,
                    error="No choices in API response",
                    model_used=model,
                )

            first_choice = cast(Any, choices_raw[0])
            if not isinstance(first_choice, dict):
                return ExtractionResult(
                    success=False,
                    error="Invalid choice format in response",
                    model_used=model,
                )

            first_choice_dict = cast(dict[str, Any], first_choice)
            message = first_choice_dict.get("message", {})
            if not isinstance(message, dict):
                return ExtractionResult(
                    success=False,
                    error="Invalid message format in response",
                    model_used=model,
                )

            message_dict = cast(dict[str, Any], message)
            content = message_dict.get("content", "")
            if not isinstance(content, str):
                return ExtractionResult(
                    success=False,
                    error="Invalid content format in response",
                    model_used=model,
                )

            # Parse JSON from content
            json_str = self._extract_json_from_response(content)

            try:
                statement = ExtractedStatement.model_validate_json(json_str)
                logger.info(f"Successfully extracted statement with model: {model}")
                return ExtractionResult(
                    success=True,
                    data=statement,
                    model_used=model,
                )
            except ValidationError as e:
                # Try to parse as raw JSON for partial data
                logger.warning(
                    f"Validation error during extraction with model {model}: {e}"
                )
                try:
                    partial = json.loads(json_str)
                    return ExtractionResult(
                        success=False,
                        partial_data=partial,
                        error=str(e),
                        model_used=model,
                    )
                except json.JSONDecodeError:
                    return ExtractionResult(
                        success=False,
                        error=f"Validation error and JSON decode failed: {e}",
                        model_used=model,
                    )

        except Exception as e:
            logger.error(f"Extraction failed with model {model}: {e}")
            return ExtractionResult(
                success=False,
                error=str(e),
                model_used=model,
            )


def provide() -> ExtractionService:
    """Provider function for dependency injection.

    Returns:
        Configured ExtractionService instance
    """
    from app.core.config import settings

    client = OpenRouterClient(api_key=settings.OPENROUTER_API_KEY)
    return ExtractionService(client)
