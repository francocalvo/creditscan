import uuid
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from sqlmodel import Session

from app.domains.card_statements.domain.models import CardStatement
from app.domains.credit_cards.domain.models import CardBrand, CreditCard
from app.domains.notifications.service.ntfy_client import NtfyClient
from app.domains.notifications.usecases.send_due_notifications.usecase import (
    SendDueNotificationsUseCase,
)
from app.domains.users.domain.models import User


def _create_user(
    db: Session,
    *,
    notifications_enabled: bool = True,
    ntfy_topic: str | None = "pf-app-test-topic",
) -> User:
    user = User(
        email=f"test-{uuid.uuid4()}@example.com",
        hashed_password="fakehash",
        notifications_enabled=notifications_enabled,
        ntfy_topic=ntfy_topic,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


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


@pytest.fixture
def mock_ntfy() -> NtfyClient:
    client = NtfyClient(server_url="http://ntfy:80")
    client.send = AsyncMock(return_value=True)
    return client


@pytest.fixture
def usecase(db: Session, mock_ntfy: NtfyClient) -> SendDueNotificationsUseCase:
    return SendDueNotificationsUseCase(
        session=db,
        ntfy_client=mock_ntfy,
        ntfy_public_url="https://ntfy.example.com",
    )


@pytest.mark.asyncio
async def test_single_statement_notification(
    db: Session, usecase: SendDueNotificationsUseCase, mock_ntfy: NtfyClient
) -> None:
    user = _create_user(db)
    card = _create_card(db, user, alias="My Visa")
    _create_statement(db, card, current_balance=Decimal("1250.00"))

    result = await usecase.execute_for_user(user.id)

    assert result.statements_found == 1
    assert result.notification_sent is True
    mock_ntfy.send.assert_called_once()
    call_kwargs = mock_ntfy.send.call_args.kwargs
    assert call_kwargs["title"] == "My Visa: Payment Due Tomorrow"
    assert "1,250.00" in call_kwargs["message"]


@pytest.mark.asyncio
async def test_multiple_statements_consolidated(
    db: Session, usecase: SendDueNotificationsUseCase, mock_ntfy: NtfyClient
) -> None:
    user = _create_user(db)
    card1 = _create_card(db, user, alias="Card A", last4="1111")
    card2 = _create_card(db, user, brand=CardBrand.MASTERCARD, last4="8888")
    _create_statement(db, card1, current_balance=Decimal("1250.00"))
    _create_statement(db, card2, current_balance=Decimal("430.50"))

    result = await usecase.execute_for_user(user.id)

    assert result.statements_found == 2
    assert result.notification_sent is True
    call_kwargs = mock_ntfy.send.call_args.kwargs
    assert call_kwargs["title"] == "2 Payments Due Tomorrow"
    assert "Card A" in call_kwargs["message"]
    assert "Mastercard ****8888" in call_kwargs["message"]


@pytest.mark.asyncio
async def test_no_statements_no_notification(
    db: Session, usecase: SendDueNotificationsUseCase, mock_ntfy: NtfyClient
) -> None:
    user = _create_user(db)

    result = await usecase.execute_for_user(user.id)

    assert result.statements_found == 0
    assert result.notification_sent is False
    mock_ntfy.send.assert_not_called()


@pytest.mark.asyncio
async def test_paid_statements_excluded(
    db: Session, usecase: SendDueNotificationsUseCase, mock_ntfy: NtfyClient
) -> None:
    user = _create_user(db)
    card = _create_card(db, user)
    _create_statement(db, card, is_fully_paid=True)

    result = await usecase.execute_for_user(user.id)

    assert result.statements_found == 0
    assert result.notification_sent is False
    mock_ntfy.send.assert_not_called()


@pytest.mark.asyncio
async def test_card_name_fallback_brand_last4(
    db: Session, usecase: SendDueNotificationsUseCase, mock_ntfy: NtfyClient
) -> None:
    user = _create_user(db)
    card = _create_card(db, user, alias=None, brand=CardBrand.AMEX, last4="9999")
    _create_statement(db, card)

    await usecase.execute_for_user(user.id)

    call_kwargs = mock_ntfy.send.call_args.kwargs
    assert "Amex ****9999" in call_kwargs["title"]


@pytest.mark.asyncio
async def test_auto_generate_ntfy_topic(
    db: Session, usecase: SendDueNotificationsUseCase
) -> None:
    user = _create_user(db, ntfy_topic=None)
    card = _create_card(db, user)
    _create_statement(db, card)

    await usecase.execute_for_user(user.id)

    db.refresh(user)
    assert user.ntfy_topic is not None
    assert user.ntfy_topic.startswith("pf-app-")


@pytest.mark.asyncio
async def test_execute_all_only_enabled_users(
    db: Session, usecase: SendDueNotificationsUseCase
) -> None:
    enabled_user = _create_user(db, notifications_enabled=True)
    disabled_user = _create_user(db, notifications_enabled=False)

    card1 = _create_card(db, enabled_user, last4="1111")
    card2 = _create_card(db, disabled_user, last4="2222")
    _create_statement(db, card1)
    _create_statement(db, card2)

    results = await usecase.execute_all()

    # Should only process the enabled user
    assert len(results) == 1
    assert results[0].user_id == enabled_user.id
    assert results[0].statements_found == 1


@pytest.mark.asyncio
async def test_statements_not_due_tomorrow_excluded(
    db: Session, usecase: SendDueNotificationsUseCase, mock_ntfy: NtfyClient
) -> None:
    user = _create_user(db)
    card = _create_card(db, user)
    # Statement due in 3 days, not tomorrow
    _create_statement(db, card, due_date=date.today() + timedelta(days=3))

    result = await usecase.execute_for_user(user.id)

    assert result.statements_found == 0
    mock_ntfy.send.assert_not_called()
