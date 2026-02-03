"""Unit tests for CardStatement model fields."""

import uuid

from app.domains.card_statements.domain.models import (
    CardStatement,
    CardStatementBase,
    CardStatementCreate,
    CardStatementUpdate,
    StatementStatus,
)


class TestStatementStatusEnum:
    """Tests for the StatementStatus enum."""

    def test_enum_has_complete_value(self):
        """StatementStatus should have COMPLETE value."""
        assert StatementStatus.COMPLETE.value == "complete"

    def test_enum_has_pending_review_value(self):
        """StatementStatus should have PENDING_REVIEW value."""
        assert StatementStatus.PENDING_REVIEW.value == "pending_review"

    def test_enum_is_string_subclass(self):
        """StatementStatus should be a str subclass for JSON serialization."""
        assert isinstance(StatementStatus.COMPLETE, str)
        assert StatementStatus.COMPLETE == "complete"


class TestCardStatementCurrency:
    """Tests for the currency field on CardStatement."""

    def test_currency_defaults_to_ars(self):
        """CardStatement should default to ARS currency."""
        statement = CardStatementBase(card_id=uuid.uuid4())
        assert statement.currency == "ARS"

    def test_currency_can_be_customized(self):
        """CardStatement should accept custom currency."""
        statement = CardStatementBase(card_id=uuid.uuid4(), currency="USD")
        assert statement.currency == "USD"


class TestCardStatementStatus:
    """Tests for the status field on CardStatement."""

    def test_status_defaults_to_complete(self):
        """CardStatement should default to COMPLETE status."""
        statement = CardStatementBase(card_id=uuid.uuid4())
        assert statement.status == StatementStatus.COMPLETE

    def test_status_can_be_pending_review(self):
        """CardStatement should accept PENDING_REVIEW status."""
        statement = CardStatementBase(
            card_id=uuid.uuid4(),
            status=StatementStatus.PENDING_REVIEW,
        )
        assert statement.status == StatementStatus.PENDING_REVIEW


class TestCardStatementSourceFilePath:
    """Tests for the source_file_path field on CardStatement."""

    def test_source_file_path_defaults_to_none(self):
        """CardStatement should default to None for source_file_path."""
        statement = CardStatementBase(card_id=uuid.uuid4())
        assert statement.source_file_path is None

    def test_source_file_path_can_be_set(self):
        """CardStatement should accept source_file_path."""
        statement = CardStatementBase(
            card_id=uuid.uuid4(),
            source_file_path="statements/user123/abc123.pdf",
        )
        assert statement.source_file_path == "statements/user123/abc123.pdf"


class TestCardStatementCreate:
    """Tests for CardStatementCreate model."""

    def test_create_inherits_new_fields(self):
        """CardStatementCreate should have all new fields with defaults."""
        statement = CardStatementCreate(card_id=uuid.uuid4())
        assert statement.currency == "ARS"
        assert statement.status == StatementStatus.COMPLETE
        assert statement.source_file_path is None


class TestCardStatementUpdate:
    """Tests for CardStatementUpdate model."""

    def test_update_has_optional_currency(self):
        """CardStatementUpdate should have optional currency field."""
        update = CardStatementUpdate()
        assert update.currency is None

        update_with_currency = CardStatementUpdate(currency="EUR")
        assert update_with_currency.currency == "EUR"

    def test_update_has_optional_status(self):
        """CardStatementUpdate should have optional status field."""
        update = CardStatementUpdate()
        assert update.status is None

        update_with_status = CardStatementUpdate(status=StatementStatus.PENDING_REVIEW)
        assert update_with_status.status == StatementStatus.PENDING_REVIEW

    def test_update_has_optional_source_file_path(self):
        """CardStatementUpdate should have optional source_file_path field."""
        update = CardStatementUpdate()
        assert update.source_file_path is None

        update_with_path = CardStatementUpdate(source_file_path="path/to/file.pdf")
        assert update_with_path.source_file_path == "path/to/file.pdf"


class TestCardStatementTableModel:
    """Tests for CardStatement table model."""

    def test_table_model_has_new_fields(self):
        """CardStatement table model should have all new fields."""
        statement = CardStatement(card_id=uuid.uuid4())
        assert statement.currency == "ARS"
        assert statement.status == StatementStatus.COMPLETE
        assert statement.source_file_path is None
