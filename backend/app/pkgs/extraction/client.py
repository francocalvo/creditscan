"""OpenRouter API client for LLM completions with PDF support."""

import base64
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """HTTP client for OpenRouter API with multimodal PDF support."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
    ) -> None:
        """Initialize OpenRouter client.

        Args:
            api_key: OpenRouter API key
            base_url: Base URL for OpenRouter API
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
        """Send PDF with prompt to OpenRouter and get completion.

        Args:
            model: Model identifier (e.g., "google/gemini-flash-1.5")
            prompt: Text prompt for the LLM
            pdf_bytes: PDF file contents as bytes
            timeout: Request timeout in seconds
            response_format: Optional response format constraint (e.g. JSON object)

        Returns:
            Parsed JSON response from OpenRouter API

        Raises:
            httpx.TimeoutException: If request exceeds timeout
            httpx.HTTPStatusError: If API returns error status
        """
        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:application/pdf;base64,{pdf_base64}"
                            },
                        },
                    ],
                }
            ],
        }
        if response_format is not None:
            payload["response_format"] = response_format

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.info(f"Sending PDF extraction request to OpenRouter with model: {model}")

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            result: dict[str, object] = response.json()
            logger.info(f"Received response from OpenRouter for model: {model}")
            return result

    async def complete_with_text(
        self,
        model: str,
        prompt: str,
        timeout: float = 120.0,
        response_format: dict[str, str] | None = None,
    ) -> dict[str, object]:
        """Send text prompt to OpenRouter and get completion.

        Args:
            model: Model identifier
            prompt: Text prompt for the LLM
            timeout: Request timeout in seconds
            response_format: Optional response format constraint (e.g. JSON object)

        Returns:
            Parsed JSON response from OpenRouter API

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

        logger.info(
            f"Sending text completion request to OpenRouter with model: {model}"
        )

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            result: dict[str, object] = response.json()
            logger.info(f"Received response from OpenRouter for model: {model}")
            return result
