"""ZAI-backed extraction provider."""

import base64
import importlib
import json
import logging
import re
from typing import Any, cast

from app.pkgs.extraction.providers.base import ExtractionPipeline

logger = logging.getLogger(__name__)


class ZaiExtractionProvider:
    """Extraction provider implementation using ZAI SDK."""

    name = "zai"

    DEFAULT_OCR_MODELS = [
        "glm-ocr",  # Primary OCR
        "glm-ocr",  # Fallback OCR
    ]
    DEFAULT_STATEMENT_MODELS = [
        "glm-4.5-air",  # Primary statement parser
        "glm-4.5-air",  # Fallback statement parser
    ]

    def __init__(
        self,
        client: Any,
        *,
        ocr_models: list[str] | None = None,
        statement_models: list[str] | None = None,
    ) -> None:
        self.client = client
        self.ocr_models = ocr_models or self.DEFAULT_OCR_MODELS.copy()
        self.statement_models = statement_models or self.DEFAULT_STATEMENT_MODELS.copy()
        self.pipelines = self._build_pipelines()

    @staticmethod
    def create_client(api_key: str) -> Any:
        """Instantiate ZaiClient lazily to avoid hard import at module import time."""
        try:
            zai_module = importlib.import_module("zai")
        except ImportError as exc:
            raise RuntimeError(
                "ZAI provider requires 'zai-sdk' to be installed"
            ) from exc

        client_cls = getattr(zai_module, "ZaiClient", None)
        if client_cls is None:
            raise RuntimeError("zai-sdk is installed but 'ZaiClient' is missing")

        return client_cls(api_key=api_key)

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
            raise ValueError("ZAI provider has no OCR->statement model pipelines")
        return pipelines

    def _split_md_results_into_pages(self, md_results: str) -> list[str]:
        """Best-effort split of ZAI markdown OCR output into page chunks."""
        parts = re.split(r"(?m)^\s*---\s*$", md_results)
        cleaned: list[str] = []
        for part in parts:
            text = part.strip()
            if not text:
                continue
            if re.fullmatch(r"(?m)#+\s*", text):
                continue
            cleaned.append(text)
        return cleaned

    def _extract_first_json_object(self, text: str) -> str | None:
        """Extract first top-level JSON object from arbitrary text."""
        start = text.find("{")
        if start == -1:
            return None

        in_str = False
        escape = False
        depth = 0
        for idx in range(start, len(text)):
            ch = text[idx]
            if in_str:
                if escape:
                    escape = False
                    continue
                if ch == "\\":
                    escape = True
                    continue
                if ch == '"':
                    in_str = False
                continue

            if ch == '"':
                in_str = True
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : idx + 1]

        return None

    def _layout_response_to_pages(self, resp: Any) -> list[dict[str, object]]:
        """Normalize ZAI layout parsing response into {page,text} entries."""
        data_info = getattr(resp, "data_info", None)
        num_pages_raw = getattr(data_info, "num_pages", None)
        expected_pages = num_pages_raw if isinstance(num_pages_raw, int) else None

        layout_details_raw = getattr(resp, "layout_details", None)
        if isinstance(layout_details_raw, list):
            layout_details = cast(list[object], layout_details_raw)
            layout_texts: list[str] = []
            for page_details_raw in layout_details:
                page_details = (
                    cast(list[object], page_details_raw)
                    if isinstance(page_details_raw, list)
                    else []
                )
                text_parts: list[str] = []
                for detail_raw in page_details:
                    content = getattr(detail_raw, "content", None)
                    if isinstance(content, str) and content:
                        text_parts.append(content)
                layout_texts.append("\n".join(text_parts).strip())

            if any(text for text in layout_texts):
                pages: list[dict[str, object]] = [
                    {"page": idx + 1, "text": layout_texts[idx]}
                    for idx in range(len(layout_texts))
                ]
                if expected_pages is not None and len(pages) < expected_pages:
                    pages.extend(
                        [
                            {"page": idx + 1, "text": ""}
                            for idx in range(len(pages), expected_pages)
                        ]
                    )
                elif expected_pages is not None and len(pages) > expected_pages:
                    pages = pages[:expected_pages]
                return pages

        md_results_raw = getattr(resp, "md_results", None)
        if isinstance(md_results_raw, str) and md_results_raw.strip():
            md_pages = self._split_md_results_into_pages(md_results_raw)
            if not md_pages:
                md_pages = [md_results_raw.strip()]

            expected = expected_pages or len(md_pages)
            if len(md_pages) < expected:
                md_pages.extend([""] * (expected - len(md_pages)))
            elif len(md_pages) > expected:
                md_pages = md_pages[:expected]

            pages = [
                {"page": idx + 1, "text": md_pages[idx]} for idx in range(expected)
            ]
            return pages

        fallback_pages = expected_pages if expected_pages and expected_pages > 0 else 1
        pages = [{"page": idx + 1, "text": ""} for idx in range(fallback_pages)]
        return pages

    async def run_ocr(
        self,
        *,
        model: str,
        prompt: str,
        pdf_bytes: bytes,
    ) -> str:
        """Run OCR model on PDF bytes and return a JSON string with pages."""
        logger.info(f"ZAI OCR call using model: {model}")
        del prompt  # layout_parsing API doesn't accept prompt text

        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        pdf_data_url = f"data:application/pdf;base64,{pdf_b64}"

        resp = self.client.layout_parsing.create(
            model=model,
            file=pdf_data_url,
        )
        pages = self._layout_response_to_pages(resp)
        return json.dumps({"pages": pages}, ensure_ascii=False)

    async def run_statement(
        self,
        *,
        model: str,
        prompt: str,
    ) -> str:
        """Run statement model and return textual JSON content."""
        logger.info(f"ZAI statement call using model: {model}")

        resp = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            do_sample=False,
            stream=False,
            temperature=0.01,
            max_tokens=40960,
            response_format={"type": "json_object"},
        )

        choices = getattr(resp, "choices", None)
        if not isinstance(choices, list) or not choices:
            raise ValueError("No choices in ZAI statement response")

        first_choice = cast(object, choices[0])
        message = getattr(first_choice, "message", None)
        content = getattr(message, "content", None)
        if isinstance(content, str) and content:
            return content

        tool_calls = getattr(message, "tool_calls", None)
        if isinstance(tool_calls, list) and tool_calls:
            first_tool_call = cast(object, tool_calls[0])
            function = getattr(first_tool_call, "function", None)
            arguments = getattr(function, "arguments", None)
            if isinstance(arguments, str) and arguments:
                return arguments

        reasoning_content = getattr(message, "reasoning_content", None)
        if isinstance(reasoning_content, str) and reasoning_content:
            extracted = self._extract_first_json_object(reasoning_content)
            if extracted:
                return extracted

        raise ValueError("ZAI statement model returned empty content")
