import logging

import httpx

logger = logging.getLogger(__name__)


class NtfyClient:
    def __init__(self, server_url: str) -> None:
        self.server_url = server_url

    async def send(
        self,
        topic: str,
        title: str,
        message: str,
        priority: int = 4,
        tags: list[str] | None = None,
    ) -> bool:
        """POST a JSON notification to the Ntfy server.

        Returns True on success (2xx), False on failure.
        """
        payload: dict = {
            "topic": topic,
            "title": title,
            "message": message,
            "priority": priority,
        }
        if tags is not None:
            payload["tags"] = tags

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.server_url, json=payload)
                response.raise_for_status()
                return True
        except Exception:
            logger.error(
                "Failed to send ntfy notification to topic %s", topic, exc_info=True
            )
            return False
