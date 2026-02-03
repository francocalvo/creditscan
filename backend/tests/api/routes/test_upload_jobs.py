"""Tests for upload jobs routes."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.routes.upload_jobs.get_job import get_upload_job
from app.domains.upload_jobs.domain.errors import UploadJobNotFoundError
from app.domains.upload_jobs.domain.models import UploadJob, UploadJobStatus


class TestGetUploadJob:
    """Tests for GET /upload-jobs/{job_id} endpoint."""

    @pytest.fixture
    def mock_current_user(self):
        """Create a mock current user."""
        user = MagicMock()
        user.id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        user.is_superuser = False
        return user

    @pytest.fixture
    def mock_other_user(self):
        """Create a mock other user."""
        user = MagicMock()
        user.id = uuid.UUID("87654321-4321-8765-4321-876543210987")
        user.is_superuser = False
        return user

    @pytest.fixture
    def mock_upload_job(self, mock_current_user):
        """Create a mock upload job."""
        job = MagicMock(spec=UploadJob)
        job.id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        job.user_id = mock_current_user.id
        job.status = UploadJobStatus.PENDING
        job.statement_id = None
        job.error_message = None
        job.created_at = "2024-01-01T00:00:00"
        job.updated_at = None
        job.completed_at = None
        return job

    @patch("app.api.routes.upload_jobs.get_job.provide_repository")
    def test_returns_own_pending_job(
        self, mock_provide_repo, mock_upload_job, mock_current_user, db
    ):
        """Test that endpoint returns own pending job."""
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = mock_upload_job
        mock_provide_repo.return_value = mock_repo

        result = get_upload_job(
            session=db,
            current_user=mock_current_user,
            job_id=mock_upload_job.id,
        )

        assert result.status == UploadJobStatus.PENDING
        assert result.id == mock_upload_job.id
        mock_repo.get_by_id.assert_called_once_with(mock_upload_job.id)

    @patch("app.api.routes.upload_jobs.get_job.provide_repository")
    def test_returns_own_completed_job(self, mock_provide_repo, mock_current_user, db):
        """Test that endpoint returns own completed job with statement_id."""
        statement_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
        job = MagicMock(spec=UploadJob)
        job.id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        job.user_id = mock_current_user.id
        job.status = UploadJobStatus.COMPLETED
        job.statement_id = statement_id
        job.error_message = None
        job.created_at = "2024-01-01T00:00:00"
        job.updated_at = "2024-01-01T00:05:00"
        job.completed_at = "2024-01-01T00:05:00"

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = job
        mock_provide_repo.return_value = mock_repo

        result = get_upload_job(
            session=db,
            current_user=mock_current_user,
            job_id=job.id,
        )

        assert result.status == UploadJobStatus.COMPLETED
        assert result.statement_id == statement_id

    @patch("app.api.routes.upload_jobs.get_job.provide_repository")
    def test_returns_own_failed_job(self, mock_provide_repo, mock_current_user, db):
        """Test that endpoint returns own failed job with error_message."""
        job = MagicMock(spec=UploadJob)
        job.id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        job.user_id = mock_current_user.id
        job.status = UploadJobStatus.FAILED
        job.statement_id = None
        job.error_message = "Extraction failed"
        job.created_at = "2024-01-01T00:00:00"
        job.updated_at = "2024-01-01T00:05:00"
        job.completed_at = "2024-01-01T00:05:00"

        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = job
        mock_provide_repo.return_value = mock_repo

        result = get_upload_job(
            session=db,
            current_user=mock_current_user,
            job_id=job.id,
        )

        assert result.status == UploadJobStatus.FAILED
        assert result.error_message == "Extraction failed"

    @patch("app.api.routes.upload_jobs.get_job.provide_repository")
    def test_returns_404_for_nonexistent_job(
        self, mock_provide_repo, mock_current_user, db
    ):
        """Test that endpoint returns 404 for non-existent job."""
        job_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        mock_repo = MagicMock()
        mock_repo.get_by_id.side_effect = UploadJobNotFoundError("Job not found")
        mock_provide_repo.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            get_upload_job(
                session=db,
                current_user=mock_current_user,
                job_id=job_id,
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Upload job not found"

    @patch("app.api.routes.upload_jobs.get_job.provide_repository")
    def test_returns_404_for_other_users_job(
        self,
        mock_provide_repo,
        mock_upload_job,
        mock_other_user,
        db,
    ):
        """Test that endpoint returns 404 for other user's job (security)."""
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = mock_upload_job
        mock_provide_repo.return_value = mock_repo

        with pytest.raises(HTTPException) as exc_info:
            get_upload_job(
                session=db,
                current_user=mock_other_user,
                job_id=mock_upload_job.id,
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Upload job not found"

    @patch("app.api.routes.upload_jobs.get_job.provide_repository")
    def test_response_matches_public_schema(
        self, mock_provide_repo, mock_upload_job, mock_current_user, db
    ):
        """Test that response matches UploadJobPublic schema."""
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = mock_upload_job
        mock_provide_repo.return_value = mock_repo

        result = get_upload_job(
            session=db,
            current_user=mock_current_user,
            job_id=mock_upload_job.id,
        )

        # Verify all required fields are present
        assert hasattr(result, "id")
        assert hasattr(result, "status")
        assert hasattr(result, "statement_id")
        assert hasattr(result, "error_message")
        assert hasattr(result, "created_at")
        assert hasattr(result, "updated_at")
        assert hasattr(result, "completed_at")
