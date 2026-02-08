"""Unit tests for UploadJob repository."""

import uuid

import pytest
from sqlmodel import Session

from app.domains.credit_cards.domain import CreditCardCreate
from app.domains.credit_cards.repository.credit_card_repository import (
    CreditCardRepository,
)
from app.domains.upload_jobs.domain.errors import (
    DuplicateFileError,
    UploadJobNotFoundError,
)
from app.domains.upload_jobs.domain.models import (
    UploadJobCreate,
    UploadJobStatus,
)
from app.domains.upload_jobs.repository import provide
from app.models import CardBrand, User, UserCreate
from app.pkgs.database import get_db_session


def create_test_user(db: Session) -> User:
    """Create a test user."""
    email = f"test-{uuid.uuid4()}@example.com"
    password = "testpassword123"
    user_in = UserCreate(email=email, password=password)
    from app.domains.users.repository import UserRepository

    user = UserRepository(db).create(user_in)
    return user


def create_test_credit_card(db: Session, user_id: uuid.UUID):
    """Create a test credit card."""
    card_in = CreditCardCreate(
        user_id=user_id,
        bank="Test Bank",
        brand=CardBrand.VISA,
        last4="1234",
        default_currency="ARS",
    )
    card = CreditCardRepository(db).create(card_in)
    return card


class TestUploadJobRepositoryCreate:
    """Tests for UploadJobRepository.create method."""

    def test_create_persists_job_with_id(self, db: Session):
        """Create should persist job and generate ID."""
        repo = provide(db)
        user = create_test_user(db)
        card = create_test_credit_card(db, user.id)

        create_data = UploadJobCreate(
            user_id=user.id,
            card_id=card.id,
            file_hash="abc123def456",
            file_path="statements/user123/file.pdf",
            file_size=1024,
        )

        job = repo.create(create_data)

        assert job.id is not None
        assert job.user_id == user.id
        assert job.card_id == card.id
        assert job.file_hash == "abc123def456"
        assert job.file_path == "statements/user123/file.pdf"
        assert job.file_size == 1024
        assert job.status == UploadJobStatus.PENDING
        assert job.retry_count == 0

    def test_create_raises_duplicate_file_error_for_same_user(self, db: Session):
        """Create should raise DuplicateFileError when file hash exists for same user."""
        repo = provide(db)
        user = create_test_user(db)
        card = create_test_credit_card(db, user.id)

        # Create first job
        create_data = UploadJobCreate(
            user_id=user.id,
            card_id=card.id,
            file_hash="abc123def456",
            file_path="statements/user123/file.pdf",
            file_size=1024,
        )
        first_job = repo.create(create_data)

        # Try to create second job with same file hash for same user
        with pytest.raises(DuplicateFileError) as exc_info:
            repo.create(create_data)

        assert "already exists for this user" in str(exc_info.value)
        assert exc_info.value.existing_job_id == first_job.id

    def test_create_allows_duplicate_hash_for_different_user(self, db: Session):
        """Create should allow same file hash for different users."""
        repo = provide(db)
        user_1 = create_test_user(db)
        user_2 = create_test_user(db)
        card_1 = create_test_credit_card(db, user_1.id)
        card_2 = create_test_credit_card(db, user_2.id)

        # Create first job for user 1
        create_data = UploadJobCreate(
            user_id=user_1.id,
            card_id=card_1.id,
            file_hash="abc123def456",
            file_path="statements/user123/file.pdf",
            file_size=1024,
        )
        repo.create(create_data)

        # Create second job for user 2 with same file hash - should succeed
        create_data_2 = UploadJobCreate(
            user_id=user_2.id,
            card_id=card_2.id,
            file_hash="abc123def456",
            file_path="statements/user456/file.pdf",
            file_size=1024,
        )
        job = repo.create(create_data_2)

        assert job.id is not None
        assert job.user_id == user_2.id

    def test_create_commits_when_session_already_in_transaction(self, db: Session):
        """Create should persist even after prior reads opened a transaction."""
        repo = provide(db)
        user = create_test_user(db)
        card = create_test_credit_card(db, user.id)

        # Prior read opens a transaction in SQLAlchemy's autobegin mode.
        _ = repo.get_by_file_hash("missing-hash", user.id)

        create_data = UploadJobCreate(
            user_id=user.id,
            card_id=card.id,
            file_hash="tx-open-hash-123",
            file_path="statements/user123/tx-open.pdf",
            file_size=2048,
        )
        created_job = repo.create(create_data)

        # Verify from an independent session that the row is committed.
        other_session = get_db_session()
        try:
            other_repo = provide(other_session)
            persisted_job = other_repo.get_by_id(created_job.id)
            assert persisted_job.id == created_job.id
            assert persisted_job.file_hash == "tx-open-hash-123"
        finally:
            other_session.close()


class TestUploadJobRepositoryGetById:
    """Tests for UploadJobRepository.get_by_id method."""

    def test_get_by_id_returns_job(self, db: Session):
        """Get by ID should return job."""
        repo = provide(db)
        user = create_test_user(db)
        card = create_test_credit_card(db, user.id)

        create_data = UploadJobCreate(
            user_id=user.id,
            card_id=card.id,
            file_hash="abc123def456",
            file_path="statements/user123/file.pdf",
            file_size=1024,
        )
        created_job = repo.create(create_data)

        job = repo.get_by_id(created_job.id)

        assert job.id == created_job.id
        assert job.user_id == user.id
        assert job.card_id == card.id

    def test_get_by_id_raises_not_found_error(self, db: Session):
        """Get by ID should raise UploadJobNotFoundError when job doesn't exist."""
        repo = provide(db)
        job_id = uuid.uuid4()

        with pytest.raises(UploadJobNotFoundError) as exc_info:
            repo.get_by_id(job_id)

        assert f"Upload job with ID {job_id} not found" in str(exc_info.value)


class TestUploadJobRepositoryGetByFileHash:
    """Tests for UploadJobRepository.get_by_file_hash method."""

    def test_get_by_file_hash_finds_duplicate(self, db: Session):
        """Get by file hash should find the existing job."""
        repo = provide(db)
        user = create_test_user(db)
        card = create_test_credit_card(db, user.id)

        create_data = UploadJobCreate(
            user_id=user.id,
            card_id=card.id,
            file_hash="abc123def456",
            file_path="statements/user123/file.pdf",
            file_size=1024,
        )
        created_job = repo.create(create_data)

        job = repo.get_by_file_hash("abc123def456", user.id)

        assert job is not None
        assert job.id == created_job.id

    def test_get_by_file_hash_returns_none_for_different_user(self, db: Session):
        """Get by file hash should return None for different user."""
        repo = provide(db)
        user = create_test_user(db)
        card = create_test_credit_card(db, user.id)

        create_data = UploadJobCreate(
            user_id=user.id,
            card_id=card.id,
            file_hash="abc123def456",
            file_path="statements/user123/file.pdf",
            file_size=1024,
        )
        repo.create(create_data)

        job = repo.get_by_file_hash("abc123def456", uuid.uuid4())

        assert job is None

    def test_get_by_file_hash_returns_none_for_nonexistent_hash(self, db: Session):
        """Get by file hash should return None for non-existent hash."""
        repo = provide(db)
        user = create_test_user(db)

        job = repo.get_by_file_hash("nonexistent123", user.id)

        assert job is None


class TestUploadJobRepositoryUpdateStatus:
    """Tests for UploadJobRepository.update_status method."""

    def test_update_status_changes_status(self, db: Session):
        """Update status should change the job status."""
        repo = provide(db)
        user = create_test_user(db)
        card = create_test_credit_card(db, user.id)

        create_data = UploadJobCreate(
            user_id=user.id,
            card_id=card.id,
            file_hash="abc123def456",
            file_path="statements/user123/file.pdf",
            file_size=1024,
        )
        job = repo.create(create_data)

        updated_job = repo.update_status(job.id, UploadJobStatus.PROCESSING)

        assert updated_job.status == UploadJobStatus.PROCESSING
        assert updated_job.updated_at is not None

    def test_update_status_sets_optional_fields(self, db: Session):
        """Update status should set optional fields when provided."""
        repo = provide(db)
        user = create_test_user(db)
        card = create_test_credit_card(db, user.id)

        create_data = UploadJobCreate(
            user_id=user.id,
            card_id=card.id,
            file_hash="abc123def456",
            file_path="statements/user123/file.pdf",
            file_size=1024,
        )
        job = repo.create(create_data)

        # Update with just completed_at (statement_id would require a valid statement)
        updated_job = repo.update_status(
            job.id,
            UploadJobStatus.COMPLETED,
            completed_at=job.created_at,
        )

        assert updated_job.status == UploadJobStatus.COMPLETED
        assert updated_job.completed_at is not None
        assert updated_job.updated_at is not None

    def test_update_status_sets_error_message(self, db: Session):
        """Update status should set error message when provided."""
        repo = provide(db)
        user = create_test_user(db)
        card = create_test_credit_card(db, user.id)

        create_data = UploadJobCreate(
            user_id=user.id,
            card_id=card.id,
            file_hash="abc123def456",
            file_path="statements/user123/file.pdf",
            file_size=1024,
        )
        job = repo.create(create_data)

        updated_job = repo.update_status(
            job.id,
            UploadJobStatus.FAILED,
            error_message="Extraction failed",
        )

        assert updated_job.status == UploadJobStatus.FAILED
        assert updated_job.error_message == "Extraction failed"
        assert updated_job.updated_at is not None
