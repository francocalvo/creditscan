"""Unit tests for storage package."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import BotoCoreError, ClientError

from app.pkgs.storage.client import StorageClient
from app.pkgs.storage.service import StorageService, provide


class TestStorageClient:
    """Tests for StorageClient."""

    def test_init_creates_s3_client(self):
        """Test that StorageClient initializes with credentials."""
        client = StorageClient(
            endpoint_url="http://localhost:3900",
            access_key="test_key",
            secret_key="test_secret",
            bucket="test-bucket",
            region="us-east-1",
        )

        assert client.bucket == "test-bucket"
        assert client.s3_client is not None
        assert client.s3_client._endpoint.host == "http://localhost:3900"

    @patch("app.pkgs.storage.client.boto3.client")
    def test_upload_stores_file_and_returns_key(self, mock_boto3_client):
        """Test that upload() stores file and returns key."""
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3

        client = StorageClient(
            endpoint_url="http://localhost:3900",
            access_key="test_key",
            secret_key="test_secret",
            bucket="test-bucket",
        )

        file_data = b"test pdf content"
        key = "statements/test-user/test-file.pdf"

        result = client.upload(key=key, data=file_data)

        assert result == key
        mock_s3.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key=key,
            Body=file_data,
            ContentType="application/pdf",
        )

    @patch("app.pkgs.storage.client.boto3.client")
    def test_upload_with_custom_content_type(self, mock_boto3_client):
        """Test that upload() accepts custom content type."""
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3

        client = StorageClient(
            endpoint_url="http://localhost:3900",
            access_key="test_key",
            secret_key="test_secret",
            bucket="test-bucket",
        )

        file_data = b"test content"
        key = "test/file.txt"

        client.upload(key=key, data=file_data, content_type="text/plain")

        mock_s3.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key=key,
            Body=file_data,
            ContentType="text/plain",
        )

    @patch("app.pkgs.storage.client.boto3.client")
    def test_upload_raises_client_error_on_failure(self, mock_boto3_client):
        """Test that upload() raises ClientError on S3 failure."""
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3
        mock_s3.put_object.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}, "PutObject"
        )

        client = StorageClient(
            endpoint_url="http://localhost:3900",
            access_key="test_key",
            secret_key="test_secret",
            bucket="test-bucket",
        )

        with pytest.raises(ClientError):
            client.upload(key="test.pdf", data=b"test data")

    @patch("app.pkgs.storage.client.boto3.client")
    def test_upload_raises_boto_core_error_on_config_failure(self, mock_boto3_client):
        """Test that upload() raises BotoCoreError on configuration error."""
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3
        mock_s3.put_object.side_effect = BotoCoreError()

        client = StorageClient(
            endpoint_url="http://localhost:3900",
            access_key="test_key",
            secret_key="test_secret",
            bucket="test-bucket",
        )

        with pytest.raises(BotoCoreError):
            client.upload(key="test.pdf", data=b"test data")

    @patch("app.pkgs.storage.client.boto3.client")
    def test_download_retrieves_file_contents(self, mock_boto3_client):
        """Test that download() retrieves file contents."""
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3

        mock_response = {"Body": MagicMock()}
        mock_response["Body"].read.return_value = b"test pdf content"
        mock_s3.get_object.return_value = mock_response

        client = StorageClient(
            endpoint_url="http://localhost:3900",
            access_key="test_key",
            secret_key="test_secret",
            bucket="test-bucket",
        )

        result = client.download(key="statements/test/test.pdf")

        assert result == b"test pdf content"
        mock_s3.get_object.assert_called_once_with(
            Bucket="test-bucket", Key="statements/test/test.pdf"
        )

    @patch("app.pkgs.storage.client.boto3.client")
    def test_download_raises_client_error_on_failure(self, mock_boto3_client):
        """Test that download() raises ClientError on S3 failure."""
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3
        mock_s3.get_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "Not Found"}}, "GetObject"
        )

        client = StorageClient(
            endpoint_url="http://localhost:3900",
            access_key="test_key",
            secret_key="test_secret",
            bucket="test-bucket",
        )

        with pytest.raises(ClientError):
            client.download(key="nonexistent.pdf")

    @patch("app.pkgs.storage.client.boto3.client")
    def test_delete_removes_file(self, mock_boto3_client):
        """Test that delete() removes file."""
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3

        client = StorageClient(
            endpoint_url="http://localhost:3900",
            access_key="test_key",
            secret_key="test_secret",
            bucket="test-bucket",
        )

        client.delete(key="statements/test/test.pdf")

        mock_s3.delete_object.assert_called_once_with(
            Bucket="test-bucket", Key="statements/test/test.pdf"
        )

    @patch("app.pkgs.storage.client.boto3.client")
    def test_delete_raises_client_error_on_failure(self, mock_boto3_client):
        """Test that delete() raises ClientError on S3 failure."""
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3
        mock_s3.delete_object.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}},
            "DeleteObject",
        )

        client = StorageClient(
            endpoint_url="http://localhost:3900",
            access_key="test_key",
            secret_key="test_secret",
            bucket="test-bucket",
        )

        with pytest.raises(ClientError):
            client.delete(key="test.pdf")


class TestStorageService:
    """Tests for StorageService."""

    @patch("app.pkgs.storage.client.boto3.client")
    def test_init_creates_service_with_client(self, mock_boto3_client):
        """Test that StorageService initializes with client."""
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3

        client = StorageClient(
            endpoint_url="http://localhost:3900",
            access_key="test_key",
            secret_key="test_secret",
            bucket="test-bucket",
        )
        service = StorageService(client=client)

        assert service.client == client

    @patch("app.pkgs.storage.client.boto3.client")
    def test_store_statement_pdf_generates_correct_key(self, mock_boto3_client):
        """Test that store_statement_pdf() generates correct key format."""
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3

        client = StorageClient(
            endpoint_url="http://localhost:3900",
            access_key="test_key",
            secret_key="test_secret",
            bucket="test-bucket",
        )
        service = StorageService(client=client)

        user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        file_hash = "abc123def456"
        file_data = b"test pdf content"

        result = service.store_statement_pdf(
            user_id=user_id, file_hash=file_hash, data=file_data
        )

        expected_key = f"statements/{user_id}/{file_hash}.pdf"
        assert result == expected_key
        mock_s3.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key=expected_key,
            Body=file_data,
            ContentType="application/pdf",
        )

    @patch("app.pkgs.storage.client.boto3.client")
    def test_get_statement_pdf_retrieves_file(self, mock_boto3_client):
        """Test that get_statement_pdf() retrieves file."""
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3

        mock_response = {"Body": MagicMock()}
        mock_response["Body"].read.return_value = b"test pdf content"
        mock_s3.get_object.return_value = mock_response

        client = StorageClient(
            endpoint_url="http://localhost:3900",
            access_key="test_key",
            secret_key="test_secret",
            bucket="test-bucket",
        )
        service = StorageService(client=client)

        key = "statements/12345678-1234-5678-1234-567812345678/abc123.pdf"
        result = service.get_statement_pdf(key=key)

        assert result == b"test pdf content"
        mock_s3.get_object.assert_called_once_with(Bucket="test-bucket", Key=key)


class TestProvideFunction:
    """Tests for the provide() function."""

    @patch("app.pkgs.storage.client.boto3.client")
    @patch("app.core.config.settings")
    def test_provide_returns_configured_service(self, mock_settings, mock_boto3_client):
        """Test that provide() returns a configured StorageService."""
        mock_settings.S3_ENDPOINT_URL = "http://localhost:3900"
        mock_settings.S3_ACCESS_KEY = "test_key"
        mock_settings.S3_SECRET_KEY = "test_secret"
        mock_settings.S3_BUCKET = "test-bucket"
        mock_settings.S3_REGION = "us-east-1"

        service = provide()

        assert isinstance(service, StorageService)
        assert isinstance(service.client, StorageClient)
        assert service.client.bucket == "test-bucket"
        mock_boto3_client.assert_called_once()
        call_kwargs = mock_boto3_client.call_args.kwargs
        assert call_kwargs["endpoint_url"] == "http://localhost:3900"
        assert call_kwargs["aws_access_key_id"] == "test_key"
        assert call_kwargs["aws_secret_access_key"] == "test_secret"
        assert call_kwargs["region_name"] == "us-east-1"
