"""Tests for upload statement endpoint."""

import hashlib
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, UploadFile

from app.api.routes.card_statements.upload_statement import upload_statement
from app.domains.credit_cards.domain.errors import CreditCardNotFoundError
from app.domains.upload_jobs.domain.errors import DuplicateFileError
from app.domains.upload_jobs.domain.models import UploadJob, UploadJobStatus


def sample_pdf_content():
    """Sample PDF file content (not a valid PDF, just bytes)."""
    return b"%PDF-1.4 fake pdf content"


def sample_txt_content():
    """Sample text file content."""
    return b"This is a text file, not a PDF."


def large_pdf_content():
    """PDF content larger than 25MB."""
    return b"0" * (25 * 1024 * 1024 + 1)


@pytest.fixture
def mock_current_user():
    """Create a mock current user."""
    user = MagicMock()
    user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
    user.is_superuser = False
    return user


@pytest.fixture
def mock_superuser():
    """Create a mock superuser."""
    user = MagicMock()
    user.id = uuid.UUID("99999999-9999-9999-9999-999999999999")
    user.is_superuser = True
    return user


@pytest.fixture
def mock_other_user():
    """Create a mock other user."""
    user = MagicMock()
    user.id = uuid.UUID("87654321-4321-8765-4321-876543210987")
    user.is_superuser = False
    return user


@pytest.fixture
def mock_card(mock_current_user):
    """Create a mock card belonging to mock_current_user."""
    card = MagicMock()
    card.id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    card.user_id = mock_current_user.id
    return card


@pytest.fixture
def mock_other_card(mock_other_user):
    """Create a mock card belonging to mock_other_user."""
    card = MagicMock()
    card.id = uuid.UUID("22222222-2222-2222-2222-222222222222")
    card.user_id = mock_other_user.id
    return card


@pytest.fixture
def mock_upload_job(mock_current_user, mock_card):
    """Create a mock upload job."""
    job = MagicMock(spec=UploadJob)
    job.id = uuid.UUID("33333333-3333-3333-3333-333333333333")
    job.user_id = mock_current_user.id
    job.card_id = mock_card.id
    job.status = UploadJobStatus.PENDING
    job.statement_id = None
    job.error_message = None
    job.created_at = "2024-01-01T00:00:00"
    job.updated_at = None
    job.completed_at = None
    return job


class TestUploadStatement:
    """Tests for POST /card-statements/upload endpoint."""

    @patch("app.api.routes.card_statements.upload_statement.provide_storage")
    @patch("app.api.routes.card_statements.upload_statement.provide_upload_job_service")
    @patch("app.api.routes.card_statements.upload_statement.provide_get_card")
    def test_rejects_non_pdf_file(
        self,
        mock_provide_get_card,
        mock_provide_job_service,
        mock_provide_storage,
        mock_card,
        mock_current_user,
        db,
    ):
        """Test that endpoint rejects non-PDF files."""
        mock_get_card = MagicMock()
        mock_get_card.execute.return_value = mock_card
        mock_provide_get_card.return_value = mock_get_card

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "statement.txt"
        mock_file.file = MagicMock()
        mock_file.file.read.return_value = sample_txt_content()

        with pytest.raises(HTTPException) as exc_info:
            upload_statement(
                session=db,
                current_user=mock_current_user,
                background_tasks=MagicMock(),
                card_id=mock_card.id,
                file=mock_file,
            )

        assert exc_info.value.status_code == 400
        assert "PDF" in exc_info.value.detail

    @patch("app.api.routes.card_statements.upload_statement.provide_storage")
    @patch("app.api.routes.card_statements.upload_statement.provide_upload_job_service")
    @patch("app.api.routes.card_statements.upload_statement.provide_get_card")
    def test_rejects_file_without_extension(
        self,
        mock_provide_get_card,
        mock_provide_job_service,
        mock_provide_storage,
        mock_card,
        mock_current_user,
        db,
    ):
        """Test that endpoint rejects files without extension."""
        mock_get_card = MagicMock()
        mock_get_card.execute.return_value = mock_card
        mock_provide_get_card.return_value = mock_get_card

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "statement"
        mock_file.file = MagicMock()
        mock_file.file.read.return_value = b"content"

        with pytest.raises(HTTPException) as exc_info:
            upload_statement(
                session=db,
                current_user=mock_current_user,
                background_tasks=MagicMock(),
                card_id=mock_card.id,
                file=mock_file,
            )

        assert exc_info.value.status_code == 400
        assert "PDF" in exc_info.value.detail

    @patch("app.api.routes.card_statements.upload_statement.provide_storage")
    @patch("app.api.routes.card_statements.upload_statement.provide_upload_job_service")
    @patch("app.api.routes.card_statements.upload_statement.provide_get_card")
    def test_rejects_oversized_file(
        self,
        mock_provide_get_card,
        mock_provide_job_service,
        mock_provide_storage,
        mock_card,
        mock_current_user,
        db,
    ):
        """Test that endpoint rejects files larger than 25MB."""
        mock_get_card = MagicMock()
        mock_get_card.execute.return_value = mock_card
        mock_provide_get_card.return_value = mock_get_card

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "statement.pdf"
        mock_file.file = MagicMock()
        mock_file.file.read.return_value = large_pdf_content()

        with pytest.raises(HTTPException) as exc_info:
            upload_statement(
                session=db,
                current_user=mock_current_user,
                background_tasks=MagicMock(),
                card_id=mock_card.id,
                file=mock_file,
            )

        assert exc_info.value.status_code == 400
        assert "size" in exc_info.value.detail

    @patch("app.api.routes.card_statements.upload_statement.provide_storage")
    @patch("app.api.routes.card_statements.upload_statement.provide_upload_job_service")
    @patch("app.api.routes.card_statements.upload_statement.provide_get_card")
    def test_rejects_upload_for_nonexistent_card(
        self,
        mock_provide_get_card,
        mock_provide_job_service,
        mock_provide_storage,
        mock_current_user,
        db,
    ):
        """Test that endpoint rejects upload for non-existent card."""
        mock_get_card = MagicMock()
        mock_get_card.execute.side_effect = CreditCardNotFoundError("Card not found")
        mock_provide_get_card.return_value = mock_get_card

        card_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "statement.pdf"
        mock_file.file = MagicMock()
        mock_file.file.read.return_value = sample_pdf_content()

        with pytest.raises(HTTPException) as exc_info:
            upload_statement(
                session=db,
                current_user=mock_current_user,
                background_tasks=MagicMock(),
                card_id=card_id,
                file=mock_file,
            )

        assert exc_info.value.status_code == 404
        assert "card not found" in exc_info.value.detail.lower()

    @patch("app.api.routes.card_statements.upload_statement.provide_storage")
    @patch("app.api.routes.card_statements.upload_statement.provide_upload_job_service")
    @patch("app.api.routes.card_statements.upload_statement.provide_get_card")
    def test_rejects_upload_for_other_users_card(
        self,
        mock_provide_get_card,
        mock_provide_job_service,
        mock_provide_storage,
        mock_other_card,
        mock_current_user,
        db,
    ):
        """Test that endpoint rejects upload for another user's card."""
        mock_get_card = MagicMock()
        mock_get_card.execute.return_value = mock_other_card
        mock_provide_get_card.return_value = mock_get_card

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "statement.pdf"
        mock_file.file = MagicMock()
        mock_file.file.read.return_value = sample_pdf_content()

        with pytest.raises(HTTPException) as exc_info:
            upload_statement(
                session=db,
                current_user=mock_current_user,
                background_tasks=MagicMock(),
                card_id=mock_other_card.id,
                file=mock_file,
            )

        assert exc_info.value.status_code == 403
        assert "own cards" in exc_info.value.detail

    @patch("app.api.routes.card_statements.upload_statement.provide_storage")
    @patch("app.api.routes.card_statements.upload_statement.provide_upload_job_service")
    @patch("app.api.routes.card_statements.upload_statement.provide_get_card")
    def test_rejects_duplicate_file(
        self,
        mock_provide_get_card,
        mock_provide_job_service,
        mock_provide_storage,
        mock_card,
        mock_current_user,
        mock_upload_job,
        db,
    ):
        """Test that endpoint rejects duplicate files."""
        mock_get_card = MagicMock()
        mock_get_card.execute.return_value = mock_card
        mock_provide_get_card.return_value = mock_get_card

        mock_job_service = MagicMock()
        existing_job_id = uuid.UUID("44444444-4444-4444-4444-444444444444")
        mock_job_service.create.side_effect = DuplicateFileError(
            "Duplicate file", existing_job_id=existing_job_id
        )
        mock_provide_job_service.return_value = mock_job_service

        mock_storage = MagicMock()
        mock_storage.store_statement_pdf.return_value = (
            "statements/12345678-1234-5678-1234-567812345678/abc123.pdf"
        )
        mock_provide_storage.return_value = mock_storage

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "statement.pdf"
        mock_file.file = MagicMock()
        mock_file.file.read.return_value = sample_pdf_content()

        with pytest.raises(HTTPException) as exc_info:
            upload_statement(
                session=db,
                current_user=mock_current_user,
                background_tasks=MagicMock(),
                card_id=mock_card.id,
                file=mock_file,
            )

        assert exc_info.value.status_code == 400
        assert "duplicate" in exc_info.value.detail.lower()
        assert str(existing_job_id) in exc_info.value.detail

    @patch("app.api.routes.card_statements.upload_statement.provide_storage")
    @patch("app.api.routes.card_statements.upload_statement.provide_upload_job_service")
    @patch("app.api.routes.card_statements.upload_statement.provide_get_card")
    def test_stores_pdf_in_storage(
        self,
        mock_provide_get_card,
        mock_provide_job_service,
        mock_provide_storage,
        mock_card,
        mock_current_user,
        mock_upload_job,
        db,
    ):
        """Test that endpoint stores PDF in storage."""
        mock_get_card = MagicMock()
        mock_get_card.execute.return_value = mock_card
        mock_provide_get_card.return_value = mock_get_card

        mock_job_service = MagicMock()
        mock_job_service.create.return_value = mock_upload_job
        mock_provide_job_service.return_value = mock_job_service

        mock_storage = MagicMock()
        mock_storage.store_statement_pdf.return_value = (
            "statements/12345678-1234-5678-1234-567812345678/abc123.pdf"
        )
        mock_provide_storage.return_value = mock_storage

        content = sample_pdf_content()
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "statement.pdf"
        mock_file.file = MagicMock()
        mock_file.file.read.return_value = content

        upload_statement(
            session=db,
            current_user=mock_current_user,
            background_tasks=MagicMock(),
            card_id=mock_card.id,
            file=mock_file,
        )

        file_hash = hashlib.sha256(content).hexdigest()
        mock_storage.store_statement_pdf.assert_called_once_with(
            mock_current_user.id, file_hash, content
        )

    @patch("app.api.routes.card_statements.upload_statement.provide_storage")
    @patch("app.api.routes.card_statements.upload_statement.provide_upload_job_service")
    @patch("app.api.routes.card_statements.upload_statement.provide_get_card")
    def test_creates_job_with_correct_data(
        self,
        mock_provide_get_card,
        mock_provide_job_service,
        mock_provide_storage,
        mock_card,
        mock_current_user,
        mock_upload_job,
        db,
    ):
        """Test that endpoint creates job with correct data."""
        mock_get_card = MagicMock()
        mock_get_card.execute.return_value = mock_card
        mock_provide_get_card.return_value = mock_get_card

        mock_job_service = MagicMock()
        mock_job_service.create.return_value = mock_upload_job
        mock_provide_job_service.return_value = mock_job_service

        mock_storage = MagicMock()
        mock_storage.store_statement_pdf.return_value = (
            "statements/12345678-1234-5678-1234-567812345678/abc123.pdf"
        )
        mock_provide_storage.return_value = mock_storage

        content = sample_pdf_content()
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "statement.pdf"
        mock_file.file = MagicMock()
        mock_file.file.read.return_value = content

        upload_statement(
            session=db,
            current_user=mock_current_user,
            background_tasks=MagicMock(),
            card_id=mock_card.id,
            file=mock_file,
        )

        file_hash = hashlib.sha256(content).hexdigest()
        file_path = f"statements/{mock_current_user.id}/{file_hash}.pdf"

        from app.domains.upload_jobs.domain.models import UploadJobCreate

        # create is called with job_create as positional arg
        assert mock_job_service.create.call_count == 1
        call_args = mock_job_service.create.call_args.args[0]
        assert isinstance(call_args, UploadJobCreate)
        assert call_args.user_id == mock_current_user.id
        assert call_args.card_id == mock_card.id
        assert call_args.file_hash == file_hash
        assert call_args.file_path == file_path
        assert call_args.file_size == len(content)

    @patch("app.api.routes.card_statements.upload_statement.provide_storage")
    @patch("app.api.routes.card_statements.upload_statement.provide_upload_job_service")
    @patch("app.api.routes.card_statements.upload_statement.provide_get_card")
    def test_schedules_background_task(
        self,
        mock_provide_get_card,
        mock_provide_job_service,
        mock_provide_storage,
        mock_card,
        mock_current_user,
        mock_upload_job,
        db,
    ):
        """Test that endpoint schedules background task."""
        mock_get_card = MagicMock()
        mock_get_card.execute.return_value = mock_card
        mock_provide_get_card.return_value = mock_get_card

        mock_job_service = MagicMock()
        mock_job_service.create.return_value = mock_upload_job
        mock_provide_job_service.return_value = mock_job_service

        mock_storage = MagicMock()
        mock_storage.store_statement_pdf.return_value = (
            "statements/12345678-1234-5678-1234-567812345678/abc123.pdf"
        )
        mock_provide_storage.return_value = mock_storage

        content = sample_pdf_content()
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "statement.pdf"
        mock_file.file = MagicMock()
        mock_file.file.read.return_value = content

        background_tasks = MagicMock()
        upload_statement(
            session=db,
            current_user=mock_current_user,
            background_tasks=background_tasks,
            card_id=mock_card.id,
            file=mock_file,
        )

        background_tasks.add_task.assert_called_once()
        call_args = background_tasks.add_task.call_args.args[0]
        assert call_args[0].__name__ == "process_upload_job"
        assert call_args[1] == mock_upload_job.id  # job_id
        assert call_args[2] == content  # pdf_bytes
        assert call_args[3] == mock_card.id  # card_id
        assert call_args[4] == mock_current_user.id  # user_id

    @patch("app.api.routes.card_statements.upload_statement.provide_storage")
    @patch("app.api.routes.card_statements.upload_statement.provide_upload_job_service")
    @patch("app.api.routes.card_statements.upload_statement.provide_get_card")
    def test_returns_202_with_job(
        self,
        mock_provide_get_card,
        mock_provide_job_service,
        mock_provide_storage,
        mock_card,
        mock_current_user,
        mock_upload_job,
        db,
    ):
        """Test that endpoint returns 202 with job."""
        mock_get_card = MagicMock()
        mock_get_card.execute.return_value = mock_card
        mock_provide_get_card.return_value = mock_get_card

        mock_job_service = MagicMock()
        mock_job_service.create.return_value = mock_upload_job
        mock_provide_job_service.return_value = mock_job_service

        mock_storage = MagicMock()
        mock_storage.store_statement_pdf.return_value = (
            "statements/12345678-1234-5678-1234-567812345678/abc123.pdf"
        )
        mock_provide_storage.return_value = mock_storage

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "statement.pdf"
        mock_file.file = MagicMock()
        mock_file.file.read.return_value = sample_pdf_content()

        result = upload_statement(
            session=db,
            current_user=mock_current_user,
            background_tasks=MagicMock(),
            card_id=mock_card.id,
            file=mock_file,
        )

        assert result.id == mock_upload_job.id
        assert result.status == UploadJobStatus.PENDING
        assert result.statement_id is None
        assert result.error_message is None

    @patch("app.api.routes.card_statements.upload_statement.provide_storage")
    @patch("app.api.routes.card_statements.upload_statement.provide_upload_job_service")
    @patch("app.api.routes.card_statements.upload_statement.provide_get_card")
    def test_file_hash_is_sha256(
        self,
        mock_provide_get_card,
        mock_provide_job_service,
        mock_provide_storage,
        mock_card,
        mock_current_user,
        mock_upload_job,
        db,
    ):
        """Test that endpoint calculates SHA-256 hash correctly."""
        mock_get_card = MagicMock()
        mock_get_card.execute.return_value = mock_card
        mock_provide_get_card.return_value = mock_get_card

        mock_job_service = MagicMock()
        mock_job_service.create.return_value = mock_upload_job
        mock_provide_job_service.return_value = mock_job_service

        mock_storage = MagicMock()
        mock_storage.store_statement_pdf.return_value = (
            "statements/12345678-1234-5678-1234-567812345678/abc123.pdf"
        )
        mock_provide_storage.return_value = mock_storage

        content = b"test content"
        expected_hash = hashlib.sha256(content).hexdigest()

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "statement.pdf"
        mock_file.file = MagicMock()
        mock_file.file.read.return_value = content

        upload_statement(
            session=db,
            current_user=mock_current_user,
            background_tasks=MagicMock(),
            card_id=mock_card.id,
            file=mock_file,
        )

        call_args = mock_job_service.create.call_args.args[0][0]
        assert call_args.file_hash == expected_hash
        mock_storage.store_statement_pdf.assert_called_once()
        storage_call_args = mock_storage.store_statement_pdf.call_args.args[0]
        assert storage_call_args[1] == expected_hash

    @patch("app.api.routes.card_statements.upload_statement.provide_storage")
    @patch("app.api.routes.card_statements.upload_statement.provide_upload_job_service")
    @patch("app.api.routes.card_statements.upload_statement.provide_get_card")
    def test_superuser_can_upload_for_any_card(
        self,
        mock_provide_get_card,
        mock_provide_job_service,
        mock_provide_storage,
        mock_other_card,
        mock_superuser,
        mock_upload_job,
        db,
    ):
        """Test that superuser can upload statements for any card."""
        mock_get_card = MagicMock()
        mock_get_card.execute.return_value = mock_other_card
        mock_provide_get_card.return_value = mock_get_card

        mock_job_service = MagicMock()
        mock_job_service.create.return_value = mock_upload_job
        mock_provide_job_service.return_value = mock_job_service

        mock_storage = MagicMock()
        mock_storage.store_statement_pdf.return_value = (
            "statements/99999999-9999-9999-9999-999999999999/abc123.pdf"
        )
        mock_provide_storage.return_value = mock_storage

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "statement.pdf"
        mock_file.file = MagicMock()
        mock_file.file.read.return_value = sample_pdf_content()

        # Should not raise 403
        result = upload_statement(
            session=db,
            current_user=mock_superuser,
            background_tasks=MagicMock(),
            card_id=mock_other_card.id,
            file=mock_file,
        )

        assert result.id == mock_upload_job.id
