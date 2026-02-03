"""Tests for the transaction tags endpoint ownership checks."""

import uuid
from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.domains.card_statements.repository import CardStatementRepository
from app.domains.credit_cards.repository import CreditCardRepository
from app.domains.tags.repository import TagRepository
from app.domains.transaction_tags.repository import TransactionTagRepository
from app.domains.transactions.repository import TransactionRepository
from app.domains.users.repository import UserRepository
from app.models import (
    CardStatementCreate,
    CreditCardCreate,
    TagCreate,
    TransactionCreate,
    TransactionTagCreate,
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


def create_test_tag(
    db: Session, user_id: uuid.UUID, label: str = "Test Tag"
) -> "TagCreate":
    """Create a test tag for a user."""
    tag_data = TagCreate(
        user_id=user_id,
        label=label,
    )
    return TagRepository(db).create(tag_data)


def create_test_transaction_tag(
    db: Session, transaction_id: uuid.UUID, tag_id: uuid.UUID
) -> "TransactionTagCreate":
    """Create a transaction-tag association."""
    tt_data = TransactionTagCreate(
        transaction_id=transaction_id,
        tag_id=tag_id,
    )
    return TransactionTagRepository(db).create(tt_data)


class TestGetTransactionTagsOwnership:
    """Tests for ownership verification when getting transaction tags."""

    def test_owner_can_get_transaction_tags(
        self, client: TestClient, db: Session
    ) -> None:
        """Test that a user can get tags for their own transaction."""
        # Create user with card, statement, transaction, and tag
        user, password = create_test_user(db)
        card = create_test_credit_card(db, user.id)
        statement = create_test_statement(db, card.id)
        transaction = create_test_transaction(db, statement.id)
        tag = create_test_tag(db, user.id, "Owner Tag")
        create_test_transaction_tag(db, transaction.id, tag.tag_id)

        headers = get_user_token_headers(client, user.email, password)

        r = client.get(
            f"{settings.API_V1_STR}/transaction-tags/transaction/{transaction.id}",
            headers=headers,
        )

        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(t["tag_id"] == str(tag.tag_id) for t in data)

    def test_non_owner_cannot_get_transaction_tags(
        self, client: TestClient, db: Session
    ) -> None:
        """Test that a user cannot get tags for another user's transaction."""
        # Create owner with card, statement, transaction, and tag
        owner, _ = create_test_user(db)
        card = create_test_credit_card(db, owner.id)
        statement = create_test_statement(db, card.id)
        transaction = create_test_transaction(db, statement.id)
        tag = create_test_tag(db, owner.id, "Owner Tag")
        create_test_transaction_tag(db, transaction.id, tag.tag_id)

        # Create another user who shouldn't have access
        other_user, other_password = create_test_user(db)
        headers = get_user_token_headers(client, other_user.email, other_password)

        r = client.get(
            f"{settings.API_V1_STR}/transaction-tags/transaction/{transaction.id}",
            headers=headers,
        )

        assert r.status_code == 403
        assert "permission" in r.json()["detail"].lower()

    def test_superuser_can_get_any_transaction_tags(
        self, client: TestClient, superuser_token_headers: dict[str, str], db: Session
    ) -> None:
        """Test that a superuser can get tags for any transaction."""
        # Create regular user with card, statement, transaction, and tag
        user, _ = create_test_user(db)
        card = create_test_credit_card(db, user.id)
        statement = create_test_statement(db, card.id)
        transaction = create_test_transaction(db, statement.id)
        tag = create_test_tag(db, user.id, "User Tag")
        create_test_transaction_tag(db, transaction.id, tag.tag_id)

        r = client.get(
            f"{settings.API_V1_STR}/transaction-tags/transaction/{transaction.id}",
            headers=superuser_token_headers,
        )

        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_transaction_not_found(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        """Test that 404 is returned for non-existent transaction."""
        fake_transaction_id = uuid.uuid4()

        r = client.get(
            f"{settings.API_V1_STR}/transaction-tags/transaction/{fake_transaction_id}",
            headers=normal_user_token_headers,
        )

        assert r.status_code == 404
        assert "transaction" in r.json()["detail"].lower()

    def test_get_tags_for_transaction_with_no_tags(
        self, client: TestClient, db: Session
    ) -> None:
        """Test getting tags for a transaction that has no tags returns empty list."""
        # Create user with card, statement, and transaction (but no tags)
        user, password = create_test_user(db)
        card = create_test_credit_card(db, user.id)
        statement = create_test_statement(db, card.id)
        transaction = create_test_transaction(db, statement.id)

        headers = get_user_token_headers(client, user.email, password)

        r = client.get(
            f"{settings.API_V1_STR}/transaction-tags/transaction/{transaction.id}",
            headers=headers,
        )

        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 0
