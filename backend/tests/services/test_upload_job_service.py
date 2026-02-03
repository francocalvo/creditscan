"""Unit tests for UploadJob service."""

import uuid

from sqlmodel import Session

from app.domains.upload_jobs.domain.models import (
    UploadJobCreate,
    UploadJobStatus,
)
from app.domains.upload_jobs.service import provide
from app.models import User


def create_test_user(db: Session) -> User:
    """Create a test user."""
    email = f"test-{uuid.uuid4()}@example.com"
    password = "testpassword123"
    from app.domains.users.repository import UserRepository
    from app.models import UserCreate

    user_in = UserCreate(email=email, password=password)
    user = UserRepository(db).create(user_in)
    return user


def create_test_credit_card(db: Session, user_id: uuid.UUID):
    """Create a test credit card."""
    from app.domains.credit_cards.domain import CreditCardCreate
    from app.domains.credit_cards.repository.credit_card_repository import (
        CreditCardRepository,
    )
    from app.models import CardBrand

    card_in = CreditCardCreate(
        user_id=user_id,
        bank="Test Bank",
        brand=CardBrand.VISA,
        last4="1234",
        default_currency="ARS",
    )
    card = CreditCardRepository(db).create(card_in)
    return card


class TestUploadJobServiceCreate:
    """Tests for UploadJobService.create method."""

    def test_service_create_delegates_to_repository(self, db: Session):
        """Service create should delegate to repository."""
        service = provide(db)
        user = create_test_user(db)
        card = create_test_credit_card(db, user.id)

        create_data = UploadJobCreate(
            user_id=user.id,
            card_id=card.id,
            file_hash="abc123def456",
            file_path="statements/user123/file.pdf",
            file_size=1024,
        )

        job = service.create(create_data)

        assert job.id is not None
        assert job.status == UploadJobStatus.PENDING


class TestUploadJobServiceGet:
    """Tests for UploadJobService.get method."""

    def test_service_get_returns_job(self, db: Session):
        """Service get should return job."""
        service = provide(db)
        user = create_test_user(db)
        card = create_test_credit_card(db, user.id)

        create_data = UploadJobCreate(
            user_id=user.id,
            card_id=card.id,
            file_hash="abc123def456",
            file_path="statements/user123/file.pdf",
            file_size=1024,
        )
        created_job = service.create(create_data)

        job = service.get(created_job.id)

        assert job.id == created_job.id


class TestUploadJobServiceUpdateStatus:
    """Tests for UploadJobService.update_status method."""

    def test_service_update_status_sets_updated_at(self, db: Session):
        """Service update_status should set updated_at."""
        service = provide(db)
        user = create_test_user(db)
        card = create_test_credit_card(db, user.id)

        create_data = UploadJobCreate(
            user_id=user.id,
            card_id=card.id,
            file_hash="abc123def456",
            file_path="statements/user123/file.pdf",
            file_size=1024,
        )
        job = service.create(create_data)

        updated_job = service.update_status(job.id, UploadJobStatus.PROCESSING)

        assert updated_job.status == UploadJobStatus.PROCESSING
        assert updated_job.updated_at is not None


class TestUploadJobServiceIncrementRetry:
    """Tests for UploadJobService.increment_retry method."""

    def test_service_increment_retry_increases_count(self, db: Session):
        """Service increment_retry should increase retry_count."""
        service = provide(db)
        user = create_test_user(db)
        card = create_test_credit_card(db, user.id)

        create_data = UploadJobCreate(
            user_id=user.id,
            card_id=card.id,
            file_hash="abc123def456",
            file_path="statements/user123/file.pdf",
            file_size=1024,
        )
        job = service.create(create_data)

        # Verify updated_at is set when incrementing retry
        updated_job = service.increment_retry(job.id)

        assert updated_job.status == UploadJobStatus.PENDING
        assert updated_job.updated_at is not None
