"""Tests for the list transactions endpoint ownership checks."""

import uuid
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.domains.card_statements.repository import CardStatementRepository
from app.domains.credit_cards.repository import CreditCardRepository
from app.domains.transactions.repository import TransactionRepository
from app.domains.users.repository import UserRepository
from app.models import (
    CardStatementCreate,
    CreditCardCreate,
    TransactionCreate,
    UserCreate,
)

from ...utils.utils import random_email, random_lower_string


def create_test_user(db: Session) -> tuple:
    """Create a test user and return (user, password)."""
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = UserRepository(db).create(user_in)
    return user, password


def get_user_token_headers(
    client: TestClient, email: str, password: str
) -> dict[str, str]:
    """Get authentication headers for a user."""
    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def create_test_credit_card(db: Session, user_id: uuid.UUID) -> "CreditCardCreate":
    """Create a test credit card for a user."""
    card_data = CreditCardCreate(
        user_id=user_id,
        bank="Test Bank",
        brand="visa",
        last4="1234",
    )
    return CreditCardRepository(db).create(card_data)


def create_test_statement(db: Session, card_id: uuid.UUID) -> "CardStatementCreate":
    """Create a test card statement."""
    statement_data = CardStatementCreate(
        card_id=card_id,
        period_start=date(2024, 1, 1),
        period_end=date(2024, 1, 31),
        close_date=date(2024, 2, 1),
        due_date=date(2024, 2, 15),
        current_balance=Decimal("100.00"),
    )
    return CardStatementRepository(db).create(statement_data)


def create_test_transaction(
    db: Session, statement_id: uuid.UUID
) -> "TransactionCreate":
    """Create a test transaction."""
    txn_data = TransactionCreate(
        statement_id=statement_id,
        txn_date=date(2024, 1, 15),
        payee="Test Payee",
        description="Test Description",
        amount=Decimal("50.00"),
        currency="USD",
    )
    return TransactionRepository(db).create(txn_data)


class TestListTransactionsOwnership:
    """Tests for ownership verification when listing transactions by statement_id."""

    def test_owner_can_list_transactions(self, client: TestClient, db: Session) -> None:
        """Test that a user can list transactions for their own statement."""
        # Create user with card, statement, and transaction
        user, password = create_test_user(db)
        card = create_test_credit_card(db, user.id)
        statement = create_test_statement(db, card.id)
        transaction = create_test_transaction(db, statement.id)

        headers = get_user_token_headers(client, user.email, password)

        r = client.get(
            f"{settings.API_V1_STR}/transactions/",
            params={"statement_id": str(statement.id)},
            headers=headers,
        )

        assert r.status_code == 200
        data = r.json()
        assert "data" in data
        assert "count" in data
        assert data["count"] >= 1
        assert any(t["id"] == str(transaction.id) for t in data["data"])

    def test_non_owner_cannot_list_transactions(
        self, client: TestClient, db: Session
    ) -> None:
        """Test that a user cannot list transactions for another user's statement."""
        # Create owner with card, statement, and transaction
        owner, _ = create_test_user(db)
        card = create_test_credit_card(db, owner.id)
        statement = create_test_statement(db, card.id)
        create_test_transaction(db, statement.id)

        # Create another user who shouldn't have access
        other_user, other_password = create_test_user(db)
        headers = get_user_token_headers(client, other_user.email, other_password)

        r = client.get(
            f"{settings.API_V1_STR}/transactions/",
            params={"statement_id": str(statement.id)},
            headers=headers,
        )

        assert r.status_code == 403
        assert "permission" in r.json()["detail"].lower()

    def test_superuser_can_list_any_transactions(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ) -> None:
        """Test that a superuser can list transactions for any statement."""
        # Create regular user with card, statement, and transaction
        user, _ = create_test_user(db)
        card = create_test_credit_card(db, user.id)
        statement = create_test_statement(db, card.id)
        transaction = create_test_transaction(db, statement.id)

        r = client.get(
            f"{settings.API_V1_STR}/transactions/",
            params={"statement_id": str(statement.id)},
            headers=superuser_token_headers,
        )

        assert r.status_code == 200
        data = r.json()
        assert data["count"] >= 1
        assert any(t["id"] == str(transaction.id) for t in data["data"])

    def test_statement_not_found(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        """Test that 404 is returned for non-existent statement."""
        fake_statement_id = uuid.uuid4()

        r = client.get(
            f"{settings.API_V1_STR}/transactions/",
            params={"statement_id": str(fake_statement_id)},
            headers=normal_user_token_headers,
        )

        assert r.status_code == 404
        assert "statement" in r.json()["detail"].lower()

    def test_list_transactions_without_statement_id(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        """Test that listing transactions without statement_id works (no ownership check)."""
        r = client.get(
            f"{settings.API_V1_STR}/transactions/",
            headers=normal_user_token_headers,
        )

        assert r.status_code == 200
        data = r.json()
        assert "data" in data
        assert "count" in data
