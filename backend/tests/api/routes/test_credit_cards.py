import uuid
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.domains.card_statements.domain.models import CardStatement, StatementStatus
from app.domains.credit_cards.domain.models import (
    CreditCard,
    CreditCardCreate,
    LimitSource,
)
from app.domains.credit_cards.repository import CreditCardRepository
from tests.utils.user import authentication_token_from_email, create_random_user


def create_test_credit_card(db: Session, user_id: uuid.UUID) -> CreditCard:
    """Create a test credit card for a user."""
    card_data = CreditCardCreate(
        user_id=user_id,
        bank="Test Bank",
        brand="visa",
        last4="1234",
    )
    return CreditCardRepository(db).create(card_data)


def create_test_statement(
    db: Session,
    card_id: uuid.UUID,
    current_balance: Decimal,
    is_fully_paid: bool = False,
) -> CardStatement:
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


def test_update_credit_limit_success(client: TestClient, db: Session) -> None:
    """Test updating credit limit successfully."""
    # Create a user and a card
    user = create_random_user(db)
    card = create_test_credit_card(db, user.id)
    headers = authentication_token_from_email(client=client, email=user.email, db=db)

    limit_value = 500000
    r = client.patch(
        f"{settings.API_V1_STR}/credit-cards/{card.id}",
        headers=headers,
        json={"credit_limit": limit_value},
    )

    assert r.status_code == 200
    data = r.json()
    assert Decimal(str(data["credit_limit"])) == Decimal(str(limit_value))
    assert data["limit_source"] == LimitSource.MANUAL.value
    assert data["limit_last_updated_at"] is not None


def test_update_credit_limit_validation(client: TestClient, db: Session) -> None:
    """Test credit limit validation."""
    user = create_random_user(db)
    card = create_test_credit_card(db, user.id)
    headers = authentication_token_from_email(client=client, email=user.email, db=db)

    # Test zero limit
    r = client.patch(
        f"{settings.API_V1_STR}/credit-cards/{card.id}",
        headers=headers,
        json={"credit_limit": 0},
    )
    assert r.status_code == 422

    # Test negative limit
    r = client.patch(
        f"{settings.API_V1_STR}/credit-cards/{card.id}",
        headers=headers,
        json={"credit_limit": -100},
    )
    assert r.status_code == 422


def test_update_credit_limit_metadata_refresh(client: TestClient, db: Session) -> None:
    """Test that limit_last_updated_at is refreshed on update."""
    user = create_random_user(db)
    card = create_test_credit_card(db, user.id)
    headers = authentication_token_from_email(client=client, email=user.email, db=db)

    # First update
    r = client.patch(
        f"{settings.API_V1_STR}/credit-cards/{card.id}",
        headers=headers,
        json={"credit_limit": 1000},
    )
    data1 = r.json()
    first_updated_at = data1["limit_last_updated_at"]

    # Second update
    r = client.patch(
        f"{settings.API_V1_STR}/credit-cards/{card.id}",
        headers=headers,
        json={"credit_limit": 2000},
    )
    data2 = r.json()
    second_updated_at = data2["limit_last_updated_at"]

    assert first_updated_at != second_updated_at


def test_update_other_fields_leaves_limit_metadata_unchanged(
    client: TestClient, db: Session
) -> None:
    """Test that updating other fields doesn't affect limit metadata."""
    user = create_random_user(db)
    card = create_test_credit_card(db, user.id)
    headers = authentication_token_from_email(client=client, email=user.email, db=db)

    # Initial limit set
    client.patch(
        f"{settings.API_V1_STR}/credit-cards/{card.id}",
        headers=headers,
        json={"credit_limit": 1000},
    )

    # Get card after initial limit
    r = client.get(f"{settings.API_V1_STR}/credit-cards/{card.id}", headers=headers)
    initial_data = r.json()

    # Update alias only
    r = client.patch(
        f"{settings.API_V1_STR}/credit-cards/{card.id}",
        headers=headers,
        json={"alias": "New Alias"},
    )

    assert r.status_code == 200
    data = r.json()
    assert data["alias"] == "New Alias"
    assert data["credit_limit"] == initial_data["credit_limit"]
    assert data["limit_source"] == initial_data["limit_source"]
    assert data["limit_last_updated_at"] == initial_data["limit_last_updated_at"]


def test_update_credit_limit_null_does_not_set_manual_source(
    client: TestClient, db: Session
) -> None:
    """Test that setting credit_limit to null does not trigger MANUAL source metadata."""
    user = create_random_user(db)
    card = create_test_credit_card(db, user.id)
    headers = authentication_token_from_email(client=client, email=user.email, db=db)

    r = client.patch(
        f"{settings.API_V1_STR}/credit-cards/{card.id}",
        headers=headers,
        json={"credit_limit": None},
    )

    assert r.status_code == 200
    data = r.json()
    assert data["credit_limit"] is None
    assert data["limit_source"] is None
    assert data["limit_last_updated_at"] is None


def test_update_credit_card_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Test updating a non-existent credit card returns 404."""
    random_id = uuid.uuid4()
    r = client.patch(
        f"{settings.API_V1_STR}/credit-cards/{random_id}",
        headers=superuser_token_headers,
        json={"credit_limit": 1000},
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "Credit card not found"


def test_get_card_outstanding_balance(client: TestClient, db: Session) -> None:
    """Test that GET /credit-cards/{id} returns correct outstanding_balance."""
    user = create_random_user(db)
    card = create_test_credit_card(db, user.id)
    headers = authentication_token_from_email(client=client, email=user.email, db=db)

    # Add unpaid and paid statements
    create_test_statement(db, card.id, Decimal("100.50"), is_fully_paid=False)
    create_test_statement(db, card.id, Decimal("200.25"), is_fully_paid=False)
    create_test_statement(db, card.id, Decimal("500.00"), is_fully_paid=True)

    r = client.get(f"{settings.API_V1_STR}/credit-cards/{card.id}", headers=headers)

    assert r.status_code == 200
    data = r.json()
    assert Decimal(str(data["outstanding_balance"])) == Decimal("300.75")


def test_list_cards_outstanding_balance(client: TestClient, db: Session) -> None:
    """Test that GET /credit-cards returns correct outstanding_balance for all cards."""
    user = create_random_user(db)
    card1 = create_test_credit_card(db, user.id)
    card2 = create_test_credit_card(db, user.id)
    headers = authentication_token_from_email(client=client, email=user.email, db=db)

    # Card 1: 300 unpaid
    create_test_statement(db, card1.id, Decimal("100.00"), is_fully_paid=False)
    create_test_statement(db, card1.id, Decimal("200.00"), is_fully_paid=False)

    # Card 2: 50 unpaid
    create_test_statement(db, card2.id, Decimal("50.00"), is_fully_paid=False)

    r = client.get(f"{settings.API_V1_STR}/credit-cards/", headers=headers)

    assert r.status_code == 200
    data = r.json()
    cards_data = data["data"]

    # Find cards in response
    card1_data = next(c for c in cards_data if c["id"] == str(card1.id))
    card2_data = next(c for c in cards_data if c["id"] == str(card2.id))

    assert Decimal(str(card1_data["outstanding_balance"])) == Decimal("300.00")
    assert Decimal(str(card2_data["outstanding_balance"])) == Decimal("50.00")
