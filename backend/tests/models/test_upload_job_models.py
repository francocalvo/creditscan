"""Unit tests for UploadJob model fields."""

import uuid

import pytest

from app.domains.upload_jobs.domain.errors import (
    DuplicateFileError,
    UploadJobError,
    UploadJobNotFoundError,
)
from app.domains.upload_jobs.domain.models import (
    UploadJob,
    UploadJobCreate,
    UploadJobPublic,
    UploadJobStatus,
)


class TestUploadJobStatusEnum:
    """Tests for the UploadJobStatus enum."""

    def test_enum_has_pending_value(self):
        """UploadJobStatus should have PENDING value."""
        assert UploadJobStatus.PENDING.value == "pending"

    def test_enum_has_processing_value(self):
        """UploadJobStatus should have PROCESSING value."""
        assert UploadJobStatus.PROCESSING.value == "processing"

    def test_enum_has_completed_value(self):
        """UploadJobStatus should have COMPLETED value."""
        assert UploadJobStatus.COMPLETED.value == "completed"

    def test_enum_has_failed_value(self):
        """UploadJobStatus should have FAILED value."""
        assert UploadJobStatus.FAILED.value == "failed"

    def test_enum_has_partial_value(self):
        """UploadJobStatus should have PARTIAL value."""
        assert UploadJobStatus.PARTIAL.value == "partial"

    def test_enum_is_string_subclass(self):
        """UploadJobStatus should be a str subclass for JSON serialization."""
        assert isinstance(UploadJobStatus.PENDING, str)
        assert UploadJobStatus.PENDING == "pending"


class TestUploadJobDefaults:
    """Tests for UploadJob default field values."""

    def test_status_defaults_to_pending(self):
        """UploadJob should default to PENDING status."""
        job = UploadJob(
            user_id=uuid.uuid4(),
            card_id=uuid.uuid4(),
            file_hash="abc123",
            file_path="statements/user123/file.pdf",
            file_size=1024,
        )
        assert job.status == UploadJobStatus.PENDING

    def test_retry_count_defaults_to_zero(self):
        """UploadJob should default retry_count to 0."""
        job = UploadJob(
            user_id=uuid.uuid4(),
            card_id=uuid.uuid4(),
            file_hash="abc123",
            file_path="statements/user123/file.pdf",
            file_size=1024,
        )
        assert job.retry_count == 0

    def test_statement_id_defaults_to_none(self):
        """UploadJob should default statement_id to None."""
        job = UploadJob(
            user_id=uuid.uuid4(),
            card_id=uuid.uuid4(),
            file_hash="abc123",
            file_path="statements/user123/file.pdf",
            file_size=1024,
        )
        assert job.statement_id is None

    def test_error_message_defaults_to_none(self):
        """UploadJob should default error_message to None."""
        job = UploadJob(
            user_id=uuid.uuid4(),
            card_id=uuid.uuid4(),
            file_hash="abc123",
            file_path="statements/user123/file.pdf",
            file_size=1024,
        )
        assert job.error_message is None

    def test_updated_at_defaults_to_none(self):
        """UploadJob should default updated_at to None."""
        job = UploadJob(
            user_id=uuid.uuid4(),
            card_id=uuid.uuid4(),
            file_hash="abc123",
            file_path="statements/user123/file.pdf",
            file_size=1024,
        )
        assert job.updated_at is None

    def test_completed_at_defaults_to_none(self):
        """UploadJob should default completed_at to None."""
        job = UploadJob(
            user_id=uuid.uuid4(),
            card_id=uuid.uuid4(),
            file_hash="abc123",
            file_path="statements/user123/file.pdf",
            file_size=1024,
        )
        assert job.completed_at is None


class TestUploadJobCreate:
    """Tests for UploadJobCreate model."""

    def test_create_has_required_fields(self):
        """UploadJobCreate should have all required fields."""
        user_id = uuid.uuid4()
        card_id = uuid.uuid4()
        create_data = UploadJobCreate(
            user_id=user_id,
            card_id=card_id,
            file_hash="abc123",
            file_path="statements/user123/file.pdf",
            file_size=1024,
        )
        assert create_data.user_id == user_id
        assert create_data.card_id == card_id
        assert create_data.file_hash == "abc123"
        assert create_data.file_path == "statements/user123/file.pdf"
        assert create_data.file_size == 1024


class TestUploadJobPublic:
    """Tests for UploadJobPublic model."""

    def test_public_excludes_internal_fields(self):
        """UploadJobPublic should exclude internal fields."""
        # Create a table model with all fields
        user_id = uuid.uuid4()
        card_id = uuid.uuid4()
        job_id = uuid.uuid4()
        statement_id = uuid.uuid4()

        job = UploadJob(
            id=job_id,
            user_id=user_id,
            card_id=card_id,
            status=UploadJobStatus.COMPLETED,
            file_hash="abc123",
            file_path="statements/user123/file.pdf",
            file_size=1024,
            statement_id=statement_id,
            error_message=None,
            retry_count=0,
        )

        # Create a public model from it
        public = UploadJobPublic.model_validate(job)

        # Public model should have these fields
        assert public.id == job_id
        assert public.status == UploadJobStatus.COMPLETED
        assert public.statement_id == statement_id
        assert public.error_message is None

        # These internal fields should NOT exist on public model
        assert not hasattr(public, "user_id")
        assert not hasattr(public, "card_id")
        assert not hasattr(public, "file_hash")
        assert not hasattr(public, "file_path")
        assert not hasattr(public, "file_size")
        assert not hasattr(public, "retry_count")


class TestUploadJobErrors:
    """Tests for UploadJob domain errors."""

    def test_upload_job_error_base_exception(self):
        """UploadJobError should be an Exception subclass."""
        assert issubclass(UploadJobError, Exception)

    def test_upload_job_not_found_error_extends_base(self):
        """UploadJobNotFoundError should extend UploadJobError."""
        assert issubclass(UploadJobNotFoundError, UploadJobError)

    def test_upload_job_not_found_error_can_be_raised(self):
        """UploadJobNotFoundError can be raised with a message."""
        with pytest.raises(UploadJobNotFoundError) as exc_info:
            raise UploadJobNotFoundError("Job not found")

        assert str(exc_info.value) == "Job not found"

    def test_duplicate_file_error_extends_base(self):
        """DuplicateFileError should extend UploadJobError."""
        assert issubclass(DuplicateFileError, UploadJobError)

    def test_duplicate_file_error_has_existing_job_id(self):
        """DuplicateFileError should have existing_job_id attribute."""
        job_id = uuid.uuid4()
        error = DuplicateFileError("Duplicate file", job_id)

        assert str(error) == "Duplicate file"
        assert error.existing_job_id == job_id
        assert error.existing_job_id == job_id


class TestUploadJobTableModel:
    """Tests for UploadJob table model."""

    def test_table_model_has_all_fields(self):
        """UploadJob table model should have all required fields."""
        user_id = uuid.uuid4()
        card_id = uuid.uuid4()
        job = UploadJob(
            user_id=user_id,
            card_id=card_id,
            file_hash="abc123",
            file_path="statements/user123/file.pdf",
            file_size=1024,
        )

        assert job.user_id == user_id
        assert job.card_id == card_id
        assert job.status == UploadJobStatus.PENDING
        assert job.file_hash == "abc123"
        assert job.file_path == "statements/user123/file.pdf"
        assert job.file_size == 1024
        assert job.retry_count == 0
        assert job.statement_id is None
        assert job.error_message is None
