"""High-level storage service for PDF statement files."""

import logging
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from app.pkgs.storage.client import StorageClient

logger = logging.getLogger(__name__)


class StorageService:
    """High-level service for storing and retrieving PDF statements."""

    def __init__(self, client: StorageClient) -> None:
        """Initialize storage service.

        Args:
            client: S3-compatible storage client
        """
        self.client = client

    def store_statement_pdf(
        self, user_id: uuid.UUID, file_hash: str, data: bytes
    ) -> str:
        """Store PDF statement for a user.

        Args:
            user_id: User's UUID
            file_hash: SHA-256 hash of the file
            data: PDF file contents as bytes

        Returns:
            Storage key in format: statements/{user_id}/{file_hash}.pdf
        """
        key = f"statements/{user_id}/{file_hash}.pdf"
        self.client.upload(key=key, data=data, content_type="application/pdf")
        logger.info(f"Stored statement PDF for user {user_id}: {key}")
        return key

    def get_statement_pdf(self, key: str) -> bytes:
        """Retrieve PDF statement by storage key.

        Args:
            key: Storage key (e.g., statements/{user_id}/{file_hash}.pdf)

        Returns:
            PDF file contents as bytes
        """
        logger.info(f"Retrieving statement PDF: {key}")
        return self.client.download(key)


def provide() -> StorageService:
    """Provider function for dependency injection.

    Returns:
        Configured StorageService instance
    """
    from app.core.config import settings

    client = StorageClient(
        endpoint_url=settings.S3_ENDPOINT_URL,
        access_key=settings.S3_ACCESS_KEY,
        secret_key=settings.S3_SECRET_KEY,
        bucket=settings.S3_BUCKET,
        region=settings.S3_REGION,
    )
    return StorageService(client)
