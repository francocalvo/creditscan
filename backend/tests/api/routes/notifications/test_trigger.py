from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.domains.card_statements.domain.models import CardStatement
from app.domains.credit_cards.domain.models import CardBrand, CreditCard
from app.domains.users.domain.models import User


def _get_test_user(db: Session) -> User:
    """Retrieve the test user created by the normal_user_token_headers fixture."""
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user is not None
    return user


def _enable_notifications(
    db: Session,
    user: User,
    ntfy_topic: str = "pf-app-test-topic",
) -> None:
    user.notifications_enabled = True
    user.ntfy_topic = ntfy_topic
    db.add(user)
    db.commit()
    db.refresh(user)


def _create_card(
    db: Session,
    user: User,
    *,
    alias: str | None = None,
    brand: CardBrand = CardBrand.VISA,
    last4: str = "4242",
) -> CreditCard:
    card = CreditCard(
        user_id=user.id,
        bank="Test Bank",
        brand=brand,
        last4=last4,
        alias=alias,
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


def _create_statement(
    db: Session,
    card: CreditCard,
    *,
    due_date: date | None = None,
    current_balance: Decimal = Decimal("1250.00"),
    is_fully_paid: bool = False,
) -> CardStatement:
    if due_date is None:
        due_date = date.today() + timedelta(days=1)
    stmt = CardStatement(
        card_id=card.id,
        due_date=due_date,
        current_balance=current_balance,
        is_fully_paid=is_fully_paid,
    )
    db.add(stmt)
    db.commit()
    db.refresh(stmt)
    return stmt


# ---------------------------------------------------------------------------
# Auth tests
# ---------------------------------------------------------------------------


def test_trigger_requires_auth(client: TestClient) -> None:
    response = client.post(f"{settings.API_V1_STR}/notifications/trigger")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Integration tests – full API → UseCase → DB flow (ntfy mocked)
# ---------------------------------------------------------------------------


def test_trigger_with_due_statement_sends_notification(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    user = _get_test_user(db)
    _enable_notifications(db, user)
    card = _create_card(db, user, alias="My Visa")
    _create_statement(db, card, current_balance=Decimal("1250.00"))

    with patch(
        "app.domains.notifications.service.ntfy_client.NtfyClient.send",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_send:
        response = client.post(
            f"{settings.API_V1_STR}/notifications/trigger",
            headers=normal_user_token_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["statements_found"] == 1
    assert data["notification_sent"] is True

    mock_send.assert_called_once()
    call_kwargs = mock_send.call_args.kwargs
    assert call_kwargs["topic"] == "pf-app-test-topic"
    assert "My Visa" in call_kwargs["title"]
    assert "1,250.00" in call_kwargs["message"]


def test_trigger_with_no_due_statements(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    user = _get_test_user(db)
    _enable_notifications(db, user)
    # No cards or statements created

    with patch(
        "app.domains.notifications.service.ntfy_client.NtfyClient.send",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_send:
        response = client.post(
            f"{settings.API_V1_STR}/notifications/trigger",
            headers=normal_user_token_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["statements_found"] == 0
    assert data["notification_sent"] is False
    mock_send.assert_not_called()


def test_trigger_skips_paid_statements(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    user = _get_test_user(db)
    _enable_notifications(db, user)
    card = _create_card(db, user)
    _create_statement(db, card, is_fully_paid=True)

    with patch(
        "app.domains.notifications.service.ntfy_client.NtfyClient.send",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_send:
        response = client.post(
            f"{settings.API_V1_STR}/notifications/trigger",
            headers=normal_user_token_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["statements_found"] == 0
    assert data["notification_sent"] is False
    mock_send.assert_not_called()


def test_trigger_with_multiple_due_statements(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    user = _get_test_user(db)
    _enable_notifications(db, user)
    card_a = _create_card(db, user, alias="Card A", last4="1111")
    card_b = _create_card(db, user, brand=CardBrand.MASTERCARD, last4="8888")
    _create_statement(db, card_a, current_balance=Decimal("500.00"))
    _create_statement(db, card_b, current_balance=Decimal("750.50"))

    with patch(
        "app.domains.notifications.service.ntfy_client.NtfyClient.send",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_send:
        response = client.post(
            f"{settings.API_V1_STR}/notifications/trigger",
            headers=normal_user_token_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["statements_found"] == 2
    assert data["notification_sent"] is True

    call_kwargs = mock_send.call_args.kwargs
    assert "2 Payments Due Tomorrow" in call_kwargs["title"]
    assert "Card A" in call_kwargs["message"]
    assert "Mastercard ****8888" in call_kwargs["message"]


def test_trigger_excludes_statements_not_due_tomorrow(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    user = _get_test_user(db)
    _enable_notifications(db, user)
    card = _create_card(db, user)
    _create_statement(db, card, due_date=date.today() + timedelta(days=3))

    with patch(
        "app.domains.notifications.service.ntfy_client.NtfyClient.send",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_send:
        response = client.post(
            f"{settings.API_V1_STR}/notifications/trigger",
            headers=normal_user_token_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["statements_found"] == 0
    assert data["notification_sent"] is False
    mock_send.assert_not_called()


def test_trigger_auto_generates_ntfy_topic(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    user = _get_test_user(db)
    user.notifications_enabled = True
    user.ntfy_topic = None
    db.add(user)
    db.commit()
    db.refresh(user)

    card = _create_card(db, user)
    _create_statement(db, card)

    with patch(
        "app.domains.notifications.service.ntfy_client.NtfyClient.send",
        new_callable=AsyncMock,
        return_value=True,
    ):
        response = client.post(
            f"{settings.API_V1_STR}/notifications/trigger",
            headers=normal_user_token_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["statements_found"] == 1
    assert data["notification_sent"] is True

    db.refresh(user)
    assert user.ntfy_topic is not None
    assert user.ntfy_topic.startswith("pf-app-")


def test_trigger_when_ntfy_service_fails(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
) -> None:
    user = _get_test_user(db)
    _enable_notifications(db, user)
    card = _create_card(db, user)
    _create_statement(db, card)

    with patch(
        "app.domains.notifications.service.ntfy_client.NtfyClient.send",
        new_callable=AsyncMock,
        return_value=False,
    ):
        response = client.post(
            f"{settings.API_V1_STR}/notifications/trigger",
            headers=normal_user_token_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["statements_found"] == 1
    assert data["notification_sent"] is False
