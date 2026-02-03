"""End-to-end tests for the upload statement workflow.

These tests verify the complete upload flow from HTTP request to database state,
with mocked external services (extraction, currency, storage).
"""

import hashlib
import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.domains.credit_cards.domain.models import CardBrand, CreditCardCreate
from app.domains.credit_cards.repository.credit_card_repository import (
    CreditCardRepository,
)
from app.domains.upload_jobs.domain.models import UploadJobStatus
from app.domains.upload_jobs.repository.upload_job_repository import (
    UploadJobRepository,
)
from app.domains.users.repository import UserRepository
from app.models import User, UserCreate
from app.pkgs.extraction.models import (
    ExtractedCycle,
    ExtractedStatement,
    ExtractedTransaction,
    ExtractionResult,
    Money,
)

from ..utils.utils import random_email, random_lower_string


# Test fixtures
def create_test_user(db: Session) -> tuple[User, str]:
    """Create a test user and return (user, password)."""
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = UserRepository(db).create(user_in)
    return user, password


def get_user_token_headers(
    client: TestClient, email: str, password: str
) -> dict[str, str]:
    """Get auth headers for a user."""
    data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=data)
    response = r.json()
    auth_token = response["access_token"]
    return {"Authorization": f"Bearer {auth_token}"}


def create_test_credit_card(
    db: Session, user_id: uuid.UUID, default_currency: str = "USD"
):
    """Create a test credit card."""
    card_in = CreditCardCreate(
        user_id=user_id,
        bank="Test Bank",
        brand=CardBrand.VISA,
        last4="1234",
        default_currency=default_currency,
    )
    return CreditCardRepository(db).create(card_in)


def sample_pdf_content() -> bytes:
    """Generate sample PDF content (fake but distinct)."""
    return b"%PDF-1.4 fake pdf content for testing " + uuid.uuid4().bytes


def create_mock_extraction_result(success: bool = True, partial: bool = False):
    """Create a mock extraction result."""
    if success:
        data = ExtractedStatement(
            statement_id="stmt-123",
            period=ExtractedCycle(
                start=date(2024, 1, 1),
                end=date(2024, 1, 31),
                due_date=date(2024, 2, 15),
            ),
            previous_balance=[Money(amount=Decimal("500.00"), currency="USD")],
            current_balance=[Money(amount=Decimal("1000.00"), currency="USD")],
            minimum_payment=[Money(amount=Decimal("50.00"), currency="USD")],
            transactions=[
                ExtractedTransaction(
                    date=date(2024, 1, 15),
                    merchant="Test Merchant",
                    amount=Money(amount=Decimal("25.00"), currency="USD"),
                    coupon=None,
                    installment=None,
                ),
                ExtractedTransaction(
                    date=date(2024, 1, 20),
                    merchant="Another Store",
                    amount=Money(amount=Decimal("75.00"), currency="USD"),
                    coupon=None,
                    installment=None,
                ),
            ],
        )
        return ExtractionResult(
            success=True, data=data, model_used="google/gemini-flash-1.5"
        )
    elif partial:
        partial_data = {
            "period": {"start": "2024-01-01", "end": "2024-01-31"},
            "current_balance": [{"amount": "1000.00", "currency": "USD"}],
            "transactions": [
                {
                    "date": "2024-01-15",
                    "merchant": "Partial Merchant",
                    "amount": {"amount": "50.00", "currency": "USD"},
                }
            ],
        }
        return ExtractionResult(
            success=False,
            partial_data=partial_data,
            error="Validation error: missing fields",
            model_used="google/gemini-flash-1.5",
        )
    else:
        return ExtractionResult(
            success=False,
            error="Failed to extract data from PDF",
            model_used="google/gemini-flash-1.5",
        )


def mock_currency_service():
    """Create a mock currency service that returns the same amount."""
    service = Mock()
    service.convert_balance = AsyncMock(
        side_effect=lambda amounts, _: sum(m.amount for m in amounts)
        if amounts
        else Decimal("0")
    )
    return service


def mock_storage_service():
    """Create a mock storage service."""
    service = Mock()
    service.store_statement_pdf = Mock(
        side_effect=lambda user_id,
        file_hash,
        _: f"statements/{user_id}/{file_hash}.pdf"
    )
    return service


class TestUploadWorkflowE2E:
    """End-to-end tests for the complete upload workflow."""

    @pytest.fixture(autouse=True)
    def setup(self, db: Session, client: TestClient):
        """Set up test fixtures for each test."""
        self.db = db
        self.client = client

        # Create test user and get auth headers
        self.user, self.password = create_test_user(db)
        self.headers = get_user_token_headers(client, self.user.email, self.password)

        # Create test credit card
        self.card = create_test_credit_card(db, self.user.id)

    def test_upload_rejects_non_pdf_file(self):
        """Given: a non-PDF file
        When: upload is attempted
        Then: returns 400 with error about PDF requirement
        """
        files = {"file": ("statement.txt", b"This is not a PDF", "text/plain")}
        data = {"card_id": str(self.card.id)}

        response = self.client.post(
            f"{settings.API_V1_STR}/card-statements/upload",
            headers=self.headers,
            files=files,
            data=data,
        )

        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    def test_upload_rejects_large_file(self):
        """Given: a PDF file larger than 25MB
        When: upload is attempted
        Then: returns 400 with error about size limit
        """
        # Create a file larger than 25MB
        large_content = b"0" * (25 * 1024 * 1024 + 1)
        files = {"file": ("large.pdf", large_content, "application/pdf")}
        data = {"card_id": str(self.card.id)}

        response = self.client.post(
            f"{settings.API_V1_STR}/card-statements/upload",
            headers=self.headers,
            files=files,
            data=data,
        )

        assert response.status_code == 400
        assert "size" in response.json()["detail"].lower()

    def test_upload_rejects_wrong_card(self):
        """Given: a card owned by a different user
        When: upload is attempted
        Then: returns 403 forbidden
        """
        # Create another user's card
        other_user, _ = create_test_user(self.db)
        other_card = create_test_credit_card(self.db, other_user.id)

        pdf_content = sample_pdf_content()
        files = {"file": ("statement.pdf", pdf_content, "application/pdf")}
        data = {"card_id": str(other_card.id)}

        response = self.client.post(
            f"{settings.API_V1_STR}/card-statements/upload",
            headers=self.headers,
            files=files,
            data=data,
        )

        assert response.status_code == 403
        assert "own cards" in response.json()["detail"]

    def test_upload_rejects_nonexistent_card(self):
        """Given: a non-existent card ID
        When: upload is attempted
        Then: returns 404 not found
        """
        pdf_content = sample_pdf_content()
        files = {"file": ("statement.pdf", pdf_content, "application/pdf")}
        data = {"card_id": str(uuid.uuid4())}

        response = self.client.post(
            f"{settings.API_V1_STR}/card-statements/upload",
            headers=self.headers,
            files=files,
            data=data,
        )

        assert response.status_code == 404
        assert "card not found" in response.json()["detail"].lower()

    @patch("app.api.routes.card_statements.upload_statement.provide_storage")
    def test_upload_creates_pending_job(self, mock_provide_storage):
        """Given: a valid PDF file
        When: upload is successful
        Then: returns 202 with job in PENDING status
        """
        mock_provide_storage.return_value = mock_storage_service()

        pdf_content = sample_pdf_content()
        files = {"file": ("statement.pdf", pdf_content, "application/pdf")}
        data = {"card_id": str(self.card.id)}

        response = self.client.post(
            f"{settings.API_V1_STR}/card-statements/upload",
            headers=self.headers,
            files=files,
            data=data,
        )

        assert response.status_code == 202
        job_data = response.json()
        assert "id" in job_data
        assert job_data["status"] == "pending"
        assert job_data["statement_id"] is None

    @patch("app.api.routes.card_statements.upload_statement.provide_storage")
    def test_upload_duplicate_rejected(self, mock_provide_storage):
        """Given: a PDF file that was already uploaded
        When: same file is uploaded again
        Then: returns 400 with duplicate error and existing job_id
        """
        mock_provide_storage.return_value = mock_storage_service()

        pdf_content = sample_pdf_content()
        files = {"file": ("statement.pdf", pdf_content, "application/pdf")}
        data = {"card_id": str(self.card.id)}

        # First upload should succeed
        response1 = self.client.post(
            f"{settings.API_V1_STR}/card-statements/upload",
            headers=self.headers,
            files=files,
            data=data,
        )
        assert response1.status_code == 202
        first_job_id = response1.json()["id"]

        # Second upload with same content should fail
        files2 = {"file": ("statement.pdf", pdf_content, "application/pdf")}
        response2 = self.client.post(
            f"{settings.API_V1_STR}/card-statements/upload",
            headers=self.headers,
            files=files2,
            data=data,
        )

        assert response2.status_code == 400
        assert "duplicate" in response2.json()["detail"].lower()
        assert first_job_id in response2.json()["detail"]


class TestJobStatusE2E:
    """End-to-end tests for job status endpoint."""

    @pytest.fixture(autouse=True)
    def setup(self, db: Session, client: TestClient):
        """Set up test fixtures."""
        self.db = db
        self.client = client

        self.user, self.password = create_test_user(db)
        self.headers = get_user_token_headers(client, self.user.email, self.password)
        self.card = create_test_credit_card(db, self.user.id)

    @patch("app.api.routes.card_statements.upload_statement.provide_storage")
    def test_get_own_job_status(self, mock_provide_storage):
        """Given: a job created by the user
        When: job status is requested
        Then: returns 200 with job details
        """
        mock_provide_storage.return_value = mock_storage_service()

        # Create a job via upload
        pdf_content = sample_pdf_content()
        files = {"file": ("statement.pdf", pdf_content, "application/pdf")}
        data = {"card_id": str(self.card.id)}

        upload_response = self.client.post(
            f"{settings.API_V1_STR}/card-statements/upload",
            headers=self.headers,
            files=files,
            data=data,
        )
        job_id = upload_response.json()["id"]

        # Get job status
        response = self.client.get(
            f"{settings.API_V1_STR}/upload-jobs/{job_id}",
            headers=self.headers,
        )

        assert response.status_code == 200
        assert response.json()["id"] == job_id
        assert "status" in response.json()

    def test_get_nonexistent_job_returns_404(self):
        """Given: a non-existent job ID
        When: job status is requested
        Then: returns 404
        """
        fake_job_id = uuid.uuid4()

        response = self.client.get(
            f"{settings.API_V1_STR}/upload-jobs/{fake_job_id}",
            headers=self.headers,
        )

        assert response.status_code == 404

    @patch("app.api.routes.card_statements.upload_statement.provide_storage")
    def test_cannot_access_other_user_job(self, mock_provide_storage):
        """Given: a job owned by another user
        When: status is requested by different user
        Then: returns 404 (security - hide existence)
        """
        mock_provide_storage.return_value = mock_storage_service()

        # Create job as first user
        pdf_content = sample_pdf_content()
        files = {"file": ("statement.pdf", pdf_content, "application/pdf")}
        data = {"card_id": str(self.card.id)}

        upload_response = self.client.post(
            f"{settings.API_V1_STR}/card-statements/upload",
            headers=self.headers,
            files=files,
            data=data,
        )
        job_id = upload_response.json()["id"]

        # Create second user
        other_user, other_password = create_test_user(self.db)
        other_headers = get_user_token_headers(
            self.client, other_user.email, other_password
        )

        # Try to access first user's job
        response = self.client.get(
            f"{settings.API_V1_STR}/upload-jobs/{job_id}",
            headers=other_headers,
        )

        # Should return 404, not 403 (hide existence for security)
        assert response.status_code == 404


class TestFullUploadFlow:
    """Tests for the complete upload-to-statement flow with mocked services."""

    @pytest.fixture(autouse=True)
    def setup(self, db: Session, client: TestClient):
        """Set up test fixtures."""
        self.db = db
        self.client = client

        self.user, self.password = create_test_user(db)
        self.headers = get_user_token_headers(client, self.user.email, self.password)
        self.card = create_test_credit_card(db, self.user.id, default_currency="USD")

    @patch("app.api.routes.card_statements.upload_statement.provide_storage")
    @patch("app.api.routes.card_statements.upload_statement.process_upload_job")
    def test_full_upload_flow_happy_path(
        self, mock_process_upload_job, mock_provide_storage
    ):
        """Given: valid PDF with successful extraction
        When: upload completes
        Then: job is created and background task is scheduled
        """
        mock_provide_storage.return_value = mock_storage_service()
        mock_process_upload_job.return_value = None  # Background task

        pdf_content = sample_pdf_content()
        files = {"file": ("statement.pdf", pdf_content, "application/pdf")}
        data = {"card_id": str(self.card.id)}

        response = self.client.post(
            f"{settings.API_V1_STR}/card-statements/upload",
            headers=self.headers,
            files=files,
            data=data,
        )

        assert response.status_code == 202
        job_data = response.json()
        assert job_data["status"] == "pending"

        # Verify job was created in database
        job_repo = UploadJobRepository(self.db)
        job = job_repo.get_by_id(uuid.UUID(job_data["id"]))
        assert job is not None
        assert job.user_id == self.user.id
        assert job.card_id == self.card.id
        assert job.status == UploadJobStatus.PENDING

    @patch("app.api.routes.card_statements.upload_statement.provide_storage")
    def test_upload_stores_file_hash(self, mock_provide_storage):
        """Given: uploaded PDF
        When: job is created
        Then: file hash is stored correctly
        """
        mock_provide_storage.return_value = mock_storage_service()

        pdf_content = sample_pdf_content()
        expected_hash = hashlib.sha256(pdf_content).hexdigest()

        files = {"file": ("statement.pdf", pdf_content, "application/pdf")}
        data = {"card_id": str(self.card.id)}

        response = self.client.post(
            f"{settings.API_V1_STR}/card-statements/upload",
            headers=self.headers,
            files=files,
            data=data,
        )

        job_id = uuid.UUID(response.json()["id"])
        job_repo = UploadJobRepository(self.db)
        job = job_repo.get_by_id(job_id)

        assert job.file_hash == expected_hash

    @patch("app.api.routes.card_statements.upload_statement.provide_storage")
    def test_upload_stores_file_size(self, mock_provide_storage):
        """Given: uploaded PDF
        When: job is created
        Then: file size is stored correctly
        """
        mock_provide_storage.return_value = mock_storage_service()

        pdf_content = sample_pdf_content()
        expected_size = len(pdf_content)

        files = {"file": ("statement.pdf", pdf_content, "application/pdf")}
        data = {"card_id": str(self.card.id)}

        response = self.client.post(
            f"{settings.API_V1_STR}/card-statements/upload",
            headers=self.headers,
            files=files,
            data=data,
        )

        job_id = uuid.UUID(response.json()["id"])
        job_repo = UploadJobRepository(self.db)
        job = job_repo.get_by_id(job_id)

        assert job.file_size == expected_size
