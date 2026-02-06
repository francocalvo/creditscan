"""Unit tests for CreditCard repository."""

import uuid
from decimal import Decimal

from sqlmodel import Session

from app.domains.card_statements.domain.models import CardStatement, StatementStatus
from app.domains.credit_cards.domain import CreditCardCreate
from app.domains.credit_cards.repository.credit_card_repository import (
    CreditCardRepository,
)
from app.models import CardBrand, User, UserCreate


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


def create_test_statement(
    db: Session,
    card_id: uuid.UUID,
    current_balance: Decimal,
    is_fully_paid: bool = False,
):
    """Create a test card statement."""
    statement = CardStatement(
        card_id=card_id,
        current_balance=current_balance,
        is_fully_paid=is_fully_paid,
        status=StatementStatus.COMPLETE,
        currency="ARS",
    )
    db.add(statement)
    db.commit()
    db.refresh(statement)
    return statement


class TestCreditCardRepositoryOutstandingBalance:
    """Tests for outstanding balance calculations in CreditCardRepository."""

    def test_get_outstanding_balance_sum_unpaid(self, db: Session):
        """Should sum current_balance of unpaid statements."""
        user = create_test_user(db)
        card = create_test_credit_card(db, user.id)
        repo = CreditCardRepository(db)

        create_test_statement(db, card.id, Decimal("100.50"), is_fully_paid=False)
        create_test_statement(db, card.id, Decimal("200.25"), is_fully_paid=False)
        create_test_statement(db, card.id, Decimal("500.00"), is_fully_paid=True)

        balance = repo.get_outstanding_balance(card.id)
        assert balance == Decimal("300.75")

    def test_get_outstanding_balance_no_statements(self, db: Session):
        """Should return 0 when no statements exist."""
        user = create_test_user(db)
        card = create_test_credit_card(db, user.id)
        repo = CreditCardRepository(db)

        balance = repo.get_outstanding_balance(card.id)
        assert balance == Decimal("0")

    def test_get_outstanding_balance_only_paid(self, db: Session):
        """Should return 0 when all statements are paid."""
        user = create_test_user(db)
        card = create_test_credit_card(db, user.id)
        repo = CreditCardRepository(db)

        create_test_statement(db, card.id, Decimal("100.00"), is_fully_paid=True)

        balance = repo.get_outstanding_balance(card.id)
        assert balance == Decimal("0")

    def test_get_outstanding_balances_bulk(self, db: Session):
        """Should return correct balances for multiple cards."""
        user = create_test_user(db)
        card1 = create_test_credit_card(db, user.id)
        card2 = create_test_credit_card(db, user.id)
        card3 = create_test_credit_card(db, user.id)
        repo = CreditCardRepository(db)

        # Card 1: 300 unpaid
        create_test_statement(db, card1.id, Decimal("100.00"), is_fully_paid=False)
        create_test_statement(db, card1.id, Decimal("200.00"), is_fully_paid=False)

        # Card 2: 50 unpaid
        create_test_statement(db, card2.id, Decimal("50.00"), is_fully_paid=False)
        create_test_statement(db, card2.id, Decimal("1000.00"), is_fully_paid=True)

        # Card 3: 0 unpaid (no statements)

        balances = repo.get_outstanding_balances([card1.id, card2.id, card3.id])

        assert balances[card1.id] == Decimal("300.00")
        assert balances[card2.id] == Decimal("50.00")
        assert balances[card3.id] == Decimal("0")

    def test_get_outstanding_balances_empty_input(self, db: Session):
        """Should return empty dict for empty input."""
        repo = CreditCardRepository(db)
        assert repo.get_outstanding_balances([]) == {}
