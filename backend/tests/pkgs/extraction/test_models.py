"""Unit tests for extraction models."""

from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.pkgs.extraction.models import (
    ExtractedCard,
    ExtractedCycle,
    ExtractedStatement,
    ExtractedTransaction,
    ExtractionResult,
    InstallmentInfo,
    Money,
)


class TestMoney:
    """Tests for Money model."""

    def test_money_validates_correctly(self):
        """Test that Money model validates with correct types."""
        money = Money(amount=Decimal("100.50"), currency="USD")

        assert money.amount == Decimal("100.50")
        assert money.currency == "USD"

    def test_money_accepts_string_amount(self):
        """Test that Money accepts string that converts to Decimal."""
        money = Money(amount="150.75", currency="ARS")  # type: ignore[arg-type]

        assert money.amount == Decimal("150.75")
        assert money.currency == "ARS"

    def test_money_accepts_int_amount(self):
        """Test that Money accepts integer amounts."""
        money = Money(amount=100, currency="EUR")  # type: ignore[arg-type]

        assert money.amount == Decimal("100")

    def test_money_requires_amount_and_currency(self):
        """Test that Money requires both fields."""
        with pytest.raises(ValidationError):
            Money(amount=Decimal("100"))  # type: ignore[call-arg]

        with pytest.raises(ValidationError):
            Money(currency="USD")  # type: ignore[call-arg]


class TestInstallmentInfo:
    """Tests for InstallmentInfo model."""

    def test_installment_info_validates_correctly(self):
        """Test that InstallmentInfo model validates correctly."""
        info = InstallmentInfo(current=1, total=12)

        assert info.current == 1
        assert info.total == 12

    def test_installment_info_requires_both_fields(self):
        """Test that InstallmentInfo requires both fields."""
        with pytest.raises(ValidationError):
            InstallmentInfo(current=1)  # type: ignore[call-arg]


class TestExtractedTransaction:
    """Tests for ExtractedTransaction model."""

    def test_transaction_accepts_all_fields(self):
        """Test that ExtractedTransaction accepts all fields."""
        tx = ExtractedTransaction(
            date=date(2025, 1, 15),
            merchant="Test Merchant",
            coupon="ABC123",
            amount=Money(amount=Decimal("50.00"), currency="USD"),
            installment=InstallmentInfo(current=1, total=3),
        )

        assert tx.date == date(2025, 1, 15)
        assert tx.merchant == "Test Merchant"
        assert tx.coupon == "ABC123"
        assert tx.amount.amount == Decimal("50.00")
        assert tx.installment is not None
        assert tx.installment.current == 1
        assert tx.installment.total == 3

    def test_transaction_with_optional_fields_omitted(self):
        """Test that ExtractedTransaction works without optional fields."""
        tx = ExtractedTransaction(
            date=date(2025, 1, 15),
            merchant="Test Merchant",
            amount=Money(amount=Decimal("50.00"), currency="USD"),
        )

        assert tx.date == date(2025, 1, 15)
        assert tx.merchant == "Test Merchant"
        assert tx.coupon is None
        assert tx.installment is None

    def test_transaction_parses_from_dict(self):
        """Test that ExtractedTransaction parses from dict."""
        data = {
            "date": "2025-01-15",
            "merchant": "Test Store",
            "amount": {"amount": 100.00, "currency": "ARS"},
        }

        tx = ExtractedTransaction.model_validate(data)

        assert tx.date == date(2025, 1, 15)
        assert tx.merchant == "Test Store"
        assert tx.amount.amount == Decimal("100")


class TestExtractedCycle:
    """Tests for ExtractedCycle model."""

    def test_cycle_validates_correctly(self):
        """Test that ExtractedCycle validates correctly."""
        cycle = ExtractedCycle(
            start=date(2025, 1, 1),
            end=date(2025, 1, 31),
            due_date=date(2025, 2, 10),
            next_cycle_start=date(2025, 2, 1),
        )

        assert cycle.start == date(2025, 1, 1)
        assert cycle.end == date(2025, 1, 31)
        assert cycle.due_date == date(2025, 2, 10)
        assert cycle.next_cycle_start == date(2025, 2, 1)

    def test_cycle_with_optional_next_cycle_omitted(self):
        """Test that ExtractedCycle works without next_cycle_start."""
        cycle = ExtractedCycle(
            start=date(2025, 1, 1),
            end=date(2025, 1, 31),
            due_date=date(2025, 2, 10),
        )

        assert cycle.next_cycle_start is None


class TestExtractedCard:
    """Tests for ExtractedCard model."""

    def test_card_with_all_fields(self):
        """Test that ExtractedCard accepts all fields."""
        card = ExtractedCard(
            last_four="1234",
            holder_name="John Doe",
        )

        assert card.last_four == "1234"
        assert card.holder_name == "John Doe"

    def test_card_with_all_fields_omitted(self):
        """Test that ExtractedCard works with no fields."""
        card = ExtractedCard()

        assert card.last_four is None
        assert card.holder_name is None


class TestExtractedStatement:
    """Tests for ExtractedStatement model."""

    def test_statement_parses_full_data(self):
        """Test that ExtractedStatement parses complete data."""
        data = {
            "statement_id": "STMT-2025-001",
            "card": {"last_four": "4321", "holder_name": "Jane Doe"},
            "period": {
                "start": "2025-01-01",
                "end": "2025-01-31",
                "due_date": "2025-02-10",
                "next_cycle_start": "2025-02-01",
            },
            "previous_balance": [{"amount": 500.00, "currency": "USD"}],
            "current_balance": [{"amount": 750.50, "currency": "USD"}],
            "minimum_payment": [{"amount": 75.00, "currency": "USD"}],
            "transactions": [
                {
                    "date": "2025-01-15",
                    "merchant": "Amazon",
                    "amount": {"amount": 250.50, "currency": "USD"},
                },
                {
                    "date": "2025-01-20",
                    "merchant": "Uber",
                    "coupon": "TRIP123",
                    "amount": {"amount": 15.00, "currency": "USD"},
                    "installment": {"current": 1, "total": 1},
                },
            ],
        }

        statement = ExtractedStatement.model_validate(data)

        assert statement.statement_id == "STMT-2025-001"
        assert statement.card is not None
        assert statement.card.last_four == "4321"
        assert statement.period.start == date(2025, 1, 1)
        assert len(statement.previous_balance) == 1
        assert len(statement.current_balance) == 1
        assert statement.current_balance[0].amount == Decimal("750.50")
        assert len(statement.transactions) == 2
        assert statement.transactions[0].merchant == "Amazon"
        assert statement.transactions[1].installment is not None

    def test_statement_with_credit_limit(self):
        """Test that ExtractedStatement parses credit_limit when present."""
        data = {
            "statement_id": "STMT-2025-001",
            "period": {
                "start": "2025-01-01",
                "end": "2025-01-31",
                "due_date": "2025-02-10",
            },
            "current_balance": [{"amount": 750.50, "currency": "USD"}],
            "credit_limit": {"amount": 5000.00, "currency": "USD"},
            "transactions": [],
        }

        statement = ExtractedStatement.model_validate(data)

        assert statement.credit_limit is not None
        assert statement.credit_limit.amount == Decimal("5000")
        assert statement.credit_limit.currency == "USD"

    def test_statement_with_null_credit_limit(self):
        """Test that ExtractedStatement handles null credit_limit."""
        data = {
            "statement_id": "STMT-2025-001",
            "period": {
                "start": "2025-01-01",
                "end": "2025-01-31",
                "due_date": "2025-02-10",
            },
            "current_balance": [{"amount": 750.50, "currency": "USD"}],
            "credit_limit": None,
            "transactions": [],
        }

        statement = ExtractedStatement.model_validate(data)

        assert statement.credit_limit is None

    def test_statement_handles_partial_data(self):
        """Test that ExtractedStatement works with missing optional fields."""
        data = {
            "statement_id": "STMT-2025-002",
            "period": {
                "start": "2025-01-01",
                "end": "2025-01-31",
                "due_date": "2025-02-10",
            },
            "current_balance": [{"amount": 100.00, "currency": "ARS"}],
            "transactions": [],
        }

        statement = ExtractedStatement.model_validate(data)

        assert statement.statement_id == "STMT-2025-002"
        assert statement.card is None
        assert statement.period.next_cycle_start is None
        assert statement.previous_balance == []
        assert statement.minimum_payment == []
        assert statement.transactions == []

    def test_statement_requires_statement_id(self):
        """Test that ExtractedStatement requires statement_id."""
        data = {
            "period": {
                "start": "2025-01-01",
                "end": "2025-01-31",
                "due_date": "2025-02-10",
            },
            "current_balance": [{"amount": 100.00, "currency": "ARS"}],
            "transactions": [],
        }

        with pytest.raises(ValidationError) as exc_info:
            ExtractedStatement.model_validate(data)

        assert "statement_id" in str(exc_info.value)

    def test_statement_parses_from_json_string(self):
        """Test that ExtractedStatement parses from JSON string."""
        json_str = """
        {
            "statement_id": "STMT-123",
            "period": {
                "start": "2025-01-01",
                "end": "2025-01-31",
                "due_date": "2025-02-10"
            },
            "current_balance": [{"amount": 200.00, "currency": "USD"}],
            "transactions": []
        }
        """

        statement = ExtractedStatement.model_validate_json(json_str)

        assert statement.statement_id == "STMT-123"
        assert statement.period.start == date(2025, 1, 1)


class TestExtractionResult:
    """Tests for ExtractionResult model."""

    def test_extraction_result_success(self):
        """Test that ExtractionResult represents success."""
        statement = ExtractedStatement(
            statement_id="STMT-001",
            period=ExtractedCycle(
                start=date(2025, 1, 1),
                end=date(2025, 1, 31),
                due_date=date(2025, 2, 10),
            ),
            current_balance=[Money(amount=Decimal("100"), currency="USD")],
            transactions=[],
        )

        result = ExtractionResult(
            success=True,
            data=statement,
            model_used="google/gemini-flash-1.5",
        )

        assert result.success is True
        assert result.data is not None
        assert result.data.statement_id == "STMT-001"
        assert result.partial_data is None
        assert result.error is None
        assert result.model_used == "google/gemini-flash-1.5"

    def test_extraction_result_failure(self):
        """Test that ExtractionResult represents failure."""
        result = ExtractionResult(
            success=False,
            error="Connection timeout",
            model_used="google/gemini-flash-1.5",
        )

        assert result.success is False
        assert result.data is None
        assert result.partial_data is None
        assert result.error == "Connection timeout"
        assert result.model_used == "google/gemini-flash-1.5"

    def test_extraction_result_partial(self):
        """Test that ExtractionResult represents partial data."""
        partial = {
            "statement_id": "STMT-001",
            "current_balance": [{"amount": 100}],  # Missing currency
        }

        result = ExtractionResult(
            success=False,
            partial_data=partial,
            error="Validation error: currency required",
            model_used="google/gemini-pro-1.5",
        )

        assert result.success is False
        assert result.data is None
        assert result.partial_data == partial
        assert result.error is not None
        assert result.model_used == "google/gemini-pro-1.5"

    def test_extraction_result_requires_model_used(self):
        """Test that ExtractionResult requires model_used."""
        with pytest.raises(ValidationError) as exc_info:
            ExtractionResult(success=True)  # type: ignore[call-arg]

        assert "model_used" in str(exc_info.value)
