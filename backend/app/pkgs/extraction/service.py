"""High-level extraction service for PDF statement parsing."""

import asyncio
import json
import logging
import re
from collections.abc import Awaitable
from contextlib import suppress
from typing import Any, TypeVar, cast

from pydantic import ValidationError

from app.core.config import settings
from app.pkgs.extraction.models import ExtractedStatement, ExtractionResult
from app.pkgs.extraction.prompt import (
    EXTRACTION_PROMPT,
    EXTRACTION_SCHEMA,
    OCR_PROMPT,
    OCR_SCHEMA,
)
from app.pkgs.extraction.providers import ExtractionProvider, provide_provider

logger = logging.getLogger(__name__)
T = TypeVar("T")


class ExtractionService:
    """Service for extracting statement data from PDF files using LLMs."""

    def __init__(
        self,
        provider: ExtractionProvider,
        *,
        wait_log_interval_seconds: float = 10.0,
    ) -> None:
        """Initialize extraction service with a provider backend."""
        self.provider = provider
        self.wait_log_interval_seconds = wait_log_interval_seconds

    async def _run_with_wait_logs(
        self,
        *,
        step: str,
        model: str,
        operation: Awaitable[T],
    ) -> T:
        """Run a provider operation with periodic heartbeat logs."""
        interval = self.wait_log_interval_seconds
        if interval <= 0:
            return await operation

        task: asyncio.Task[T] = asyncio.create_task(operation)
        start = asyncio.get_running_loop().time()
        heartbeat = 0
        try:
            while True:
                try:
                    return await asyncio.wait_for(
                        asyncio.shield(task), timeout=interval
                    )
                except TimeoutError:
                    heartbeat += 1
                    elapsed = asyncio.get_running_loop().time() - start
                    logger.info(
                        "Still waiting on model response: "
                        "step=%s provider=%s model=%s elapsed=%.1fs heartbeat=%s",
                        step,
                        self.provider.name,
                        model,
                        elapsed,
                        heartbeat,
                    )
        finally:
            if not task.done():
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task

    def _pipeline_count(self) -> int:
        """Get total available OCR->statement model pipelines."""
        return len(self.provider.pipelines)

    def _build_ocr_prompt(self) -> str:
        """Build the OCR prompt with schema."""
        schema_str = json.dumps(OCR_SCHEMA, indent=2)
        return f"{OCR_PROMPT}\n{schema_str}"

    def _build_statement_prompt(self, ocr_pages: list[dict[str, Any]]) -> str:
        """Build the statement extraction prompt from OCR pages.

        Returns:
            Complete prompt string with schema appended
        """
        schema_str = json.dumps(EXTRACTION_SCHEMA, indent=2)
        ocr_payload = json.dumps({"pages": ocr_pages}, ensure_ascii=False)
        return (
            f"{EXTRACTION_PROMPT}\n{schema_str}\n\n"
            "OCR_TEXT (JSON with pages):\n"
            f"{ocr_payload}\n\n"
            "Now fill the schema using the OCR_TEXT above."
        )

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

    def _parse_ocr_pages(self, ocr_json: str) -> list[dict[str, Any]]:
        """Parse OCR output JSON into normalized pages."""
        payload_raw = json.loads(ocr_json)
        if not isinstance(payload_raw, dict):
            raise ValueError("OCR response is not a JSON object")
        payload = cast(dict[str, object], payload_raw)

        pages_raw = payload.get("pages")
        if not isinstance(pages_raw, list):
            raise ValueError("OCR response missing 'pages' list")
        pages_list = cast(list[object], pages_raw)

        pages: list[dict[str, Any]] = []
        for idx, item_raw in enumerate(pages_list, start=1):
            if not isinstance(item_raw, dict):
                continue
            item = cast(dict[str, object], item_raw)

            page_value = item.get("page")
            page_num: int
            if isinstance(page_value, int):
                page_num = page_value
            else:
                try:
                    page_num = int(str(page_value))
                except (TypeError, ValueError):
                    page_num = idx

            text_value_obj = item.get("text", "")
            text = (
                text_value_obj
                if isinstance(text_value_obj, str)
                else str(text_value_obj)
            )
            pages.append({"page": page_num, "text": text})

        if not pages:
            raise ValueError("OCR response contains no valid pages")

        pages.sort(key=lambda p: int(p["page"]))
        return pages

    async def extract_statement(
        self,
        pdf_bytes: bytes,
        model_index: int = 0,
    ) -> ExtractionResult:
        """Extract statement data from PDF.

        Args:
            pdf_bytes: PDF file contents
            model_index: Index into OCR->statement model pipelines

        Returns:
            ExtractionResult with success/failure state and data
        """
        if model_index >= self._pipeline_count():
            return ExtractionResult(
                success=False,
                error="No more models available for extraction",
                model_used="none",
            )

        pipeline = self.provider.pipelines[model_index]
        ocr_model = pipeline.ocr_model
        statement_model = pipeline.statement_model
        model_used = (
            f"provider={self.provider.name};ocr={ocr_model};statement={statement_model}"
        )
        ocr_prompt = self._build_ocr_prompt()

        try:
            logger.info(
                "Starting OCR extraction with provider/model: "
                f"{self.provider.name}/{ocr_model}"
            )
            ocr_content = await self._run_with_wait_logs(
                step="ocr",
                model=ocr_model,
                operation=self.provider.run_ocr(
                    model=ocr_model,
                    prompt=ocr_prompt,
                    pdf_bytes=pdf_bytes,
                ),
            )
            ocr_json_str = self._extract_json_from_response(ocr_content)
            ocr_pages = self._parse_ocr_pages(ocr_json_str)

            logger.info(
                "Starting statement extraction with provider/model: "
                f"{self.provider.name}/{statement_model}"
            )
            statement_prompt = self._build_statement_prompt(ocr_pages)
            content = await self._run_with_wait_logs(
                step="statement",
                model=statement_model,
                operation=self.provider.run_statement(
                    model=statement_model,
                    prompt=statement_prompt,
                ),
            )
            json_str = self._extract_json_from_response(content)

            try:
                statement = ExtractedStatement.model_validate_json(json_str)
                logger.info(
                    "Successfully extracted statement with OCR->statement pipeline: "
                    f"{model_used}"
                )
                return ExtractionResult(
                    success=True,
                    data=statement,
                    model_used=model_used,
                )
            except ValidationError as e:
                # Try to parse as raw JSON for partial data
                logger.warning(
                    f"Validation error during statement extraction with {model_used}: {e}"
                )
                try:
                    partial = json.loads(json_str)
                    return ExtractionResult(
                        success=False,
                        partial_data=partial,
                        error=str(e),
                        model_used=model_used,
                    )
                except json.JSONDecodeError:
                    return ExtractionResult(
                        success=False,
                        error=f"Validation error and JSON decode failed: {e}",
                        model_used=model_used,
                    )

        except Exception as e:
            logger.error(f"Extraction failed with pipeline {model_used}: {e}")
            return ExtractionResult(
                success=False,
                error=str(e),
                model_used=model_used,
            )


def provide() -> ExtractionService:
    """Provider function for dependency injection.

    Returns:
        Configured ExtractionService instance
    """
    return ExtractionService(
        provide_provider(),
        wait_log_interval_seconds=settings.EXTRACTION_WAIT_LOG_INTERVAL_SECONDS,
    )
