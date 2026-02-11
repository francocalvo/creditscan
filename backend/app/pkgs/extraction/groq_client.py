"""Groq API client for LLM completions with multimodal support."""

import base64
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)
MAX_GROQ_OCR_PAGES = 8
GROQ_OCR_DPI = 150


class GroqClient:
    """HTTP client for Groq API with multimodal PDF support."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.groq.com/openai/v1",
    ) -> None:
        """Initialize Groq client.

        Args:
            api_key: Groq API key
            base_url: Base URL for Groq API
        """
        self.api_key = api_key
        self.base_url = base_url

    async def complete_with_pdf(
        self,
        model: str,
        prompt: str,
        pdf_bytes: bytes,
        timeout: float = 120.0,
        response_format: dict[str, str] | None = None,
    ) -> dict[str, object]:
        """Send PDF with prompt to Groq and get completion.

        Args:
            model: Model identifier (e.g., "meta-llama/llama-4-maverick-17b-128e-instruct")
            prompt: Text prompt for the LLM
            pdf_bytes: PDF file contents as bytes
            timeout: Request timeout in seconds
            response_format: Optional response format constraint (e.g. JSON object)

        Returns:
            Parsed JSON response from Groq API

        Raises:
            httpx.TimeoutException: If request exceeds timeout
            httpx.HTTPStatusError: If API returns error status
        """
        image_data_urls = self._pdf_to_png_data_urls(pdf_bytes)
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        content.extend(
            {"type": "image_url", "image_url": {"url": image_data_url}}
            for image_data_url in image_data_urls
        )

        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": content,
                }
            ],
        }
        if response_format is not None:
            payload["response_format"] = response_format

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.info(f"Sending PDF extraction request to Groq with model: {model}")

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            result: dict[str, object] = response.json()
            logger.info(f"Received response from Groq for model: {model}")
            return result

    def _pdf_to_png_data_urls(
        self,
        pdf_bytes: bytes,
        *,
        max_pages: int = MAX_GROQ_OCR_PAGES,
        dpi: int = GROQ_OCR_DPI,
    ) -> list[str]:
        """Render PDF pages into PNG data URLs for Groq Vision.

        Groq vision accepts image inputs but not raw PDF data URLs, so we convert
        each page to a PNG and send it as an image_url item.
        """
        try:
            import fitz  # PyMuPDF
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise RuntimeError(
                "PyMuPDF is required for Groq OCR PDF conversion. "
                "Install dependency 'pymupdf'."
            ) from exc

        document = fitz.open(stream=pdf_bytes, filetype="pdf")
        try:
            if document.page_count == 0:
                raise ValueError("PDF has no pages")

            page_count = min(document.page_count, max_pages)
            if document.page_count > max_pages:
                logger.warning(
                    "Groq OCR PDF has %s pages; truncating to first %s pages",
                    document.page_count,
                    max_pages,
                )

            zoom = dpi / 72.0
            matrix = fitz.Matrix(zoom, zoom)
            images: list[str] = []
            for page_index in range(page_count):
                page = document.load_page(page_index)
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                image_bytes = pixmap.tobytes("png")
                image_base64 = base64.b64encode(image_bytes).decode("utf-8")
                images.append(f"data:image/png;base64,{image_base64}")

            if not images:
                raise ValueError("PDF conversion produced no images")
            return images
        finally:
            document.close()

    async def complete_with_text(
        self,
        model: str,
        prompt: str,
        timeout: float = 120.0,
        response_format: dict[str, str] | None = None,
    ) -> dict[str, object]:
        """Send text prompt to Groq and get completion.

        Args:
            model: Model identifier
            prompt: Text prompt for the LLM
            timeout: Request timeout in seconds
            response_format: Optional response format constraint (e.g. JSON object)

        Returns:
            Parsed JSON response from Groq API

        Raises:
            httpx.TimeoutException: If request exceeds timeout
            httpx.HTTPStatusError: If API returns error status
        """
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }
        if response_format is not None:
            payload["response_format"] = response_format

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.info(f"Sending text completion request to Groq with model: {model}")

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            result: dict[str, object] = response.json()
            logger.info(f"Received response from Groq for model: {model}")
            return result
