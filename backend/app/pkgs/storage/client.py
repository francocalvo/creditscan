"""S3/Garage-compatible storage client for PDF files."""

import logging
from typing import TYPE_CHECKING

import boto3  # type: ignore[reportUnknownMemberType]
from botocore.client import Config  # type: ignore[reportUnknownMemberType]
from botocore.exceptions import (  # type: ignore[reportUnknownMemberType]
    BotoCoreError,
    ClientError,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class StorageClient:
    """S3-compatible storage client for PDF storage."""

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        region: str = "us-east-1",
    ) -> None:
        """Initialize S3 client with credentials.

        Args:
            endpoint_url: S3-compatible endpoint URL
            access_key: Access key ID
            secret_key: Secret access key
            bucket: S3 bucket name
            region: AWS region (default: us-east-1)
        """
        self.bucket = bucket

        # Create S3 client with s3v4 signature for Garage compatibility
        self.s3_client = boto3.client(  # type: ignore[reportUnknownMemberType]
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            config=Config(signature_version="s3v4"),
        )
        logger.info(f"StorageClient initialized for bucket: {bucket}")

    def upload(
        self, key: str, data: bytes, content_type: str = "application/pdf"
    ) -> str:
        """Upload file to S3-compatible storage.

        Args:
            key: Storage key (path)
            data: File contents as bytes
            content_type: MIME type (default: application/pdf)

        Returns:
            The storage key

        Raises:
            ClientError: If upload fails
            BotoCoreError: If there's a boto3 configuration error
        """
        try:
            self.s3_client.put_object(  # type: ignore[reportUnknownMemberType]
                Bucket=self.bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
            logger.info(f"Uploaded file to storage: {key}")
            return key
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to upload file {key}: {e}")
            raise

    def download(self, key: str) -> bytes:
        """Download file from S3-compatible storage.

        Args:
            key: Storage key (path)

        Returns:
            File contents as bytes

        Raises:
            ClientError: If file doesn't exist or download fails
            BotoCoreError: If there's a boto3 configuration error
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)  # type: ignore[reportUnknownMemberType]
            content = response["Body"].read()  # type: ignore[reportUnknownMemberType]
            logger.info(f"Downloaded file from storage: {key}")
            return content  # type: ignore[reportUnknownVariableType]
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to download file {key}: {e}")
            raise

    def delete(self, key: str) -> None:
        """Delete file from S3-compatible storage.

        Args:
            key: Storage key (path)

        Raises:
            ClientError: If deletion fails
            BotoCoreError: If there's a boto3 configuration error
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=key)  # type: ignore[reportUnknownMemberType]
            logger.info(f"Deleted file from storage: {key}")
        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to delete file {key}: {e}")
            raise
