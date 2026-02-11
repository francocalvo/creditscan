"""Integration tests for the notification flow.

These tests exercise the full Scheduler → UseCase → DB pipeline with a real
database session, only mocking the external ntfy HTTP calls.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlmodel import Session

from app.domains.card_statements.domain.models import CardStatement
from app.domains.credit_cards.domain.models import CardBrand, CreditCard
from app.domains.notifications.service.notification_scheduler import (
    NotificationScheduler,
)
from app.domains.notifications.service.ntfy_client import NtfyClient
from app.domains.users.domain.models import User

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


def _build_session_factory(db: Session):
    """Return a factory whose context manager yields the test session."""
    wrapper = MagicMock()
    wrapper.__enter__ = MagicMock(return_value=db)
    wrapper.__exit__ = MagicMock(return_value=False)
    return MagicMock(return_value=wrapper)


# ---------------------------------------------------------------------------
# Scheduler._execute integration tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_sends_notifications_for_enabled_users(
    db: Session,
) -> None:
    """Scheduler execute processes enabled users with due statements."""
    user = _create_user(db)
    card = _create_card(db, user, alias="My Visa")
    _create_statement(db, card, current_balance=Decimal("800.00"))

    mock_ntfy = NtfyClient(server_url="https://ntfy.sh")
    mock_ntfy.send = AsyncMock(return_value=True)

    scheduler = NotificationScheduler(
        session_factory=_build_session_factory(db),
        ntfy_client_factory=lambda: mock_ntfy,
    )

    await scheduler._execute()

    mock_ntfy.send.assert_called_once()
    call_kwargs = mock_ntfy.send.call_args.kwargs
    assert call_kwargs["topic"] == "pf-app-test-topic"
    assert "My Visa" in call_kwargs["title"]
    assert "800.00" in call_kwargs["message"]


@pytest.mark.asyncio
async def test_execute_skips_disabled_users(db: Session) -> None:
    """Scheduler execute ignores users with notifications_enabled=False."""
    _enabled = _create_user(db, notifications_enabled=True)
    disabled = _create_user(db, notifications_enabled=False)

    card_enabled = _create_card(db, _enabled, last4="1111")
    card_disabled = _create_card(db, disabled, last4="2222")
    _create_statement(db, card_enabled)
    _create_statement(db, card_disabled)

    mock_ntfy = NtfyClient(server_url="https://ntfy.sh")
    mock_ntfy.send = AsyncMock(return_value=True)

    scheduler = NotificationScheduler(
        session_factory=_build_session_factory(db),
        ntfy_client_factory=lambda: mock_ntfy,
    )

    await scheduler._execute()

    # Only the enabled user should trigger a notification
    mock_ntfy.send.assert_called_once()


@pytest.mark.asyncio
async def test_execute_handles_multiple_users(db: Session) -> None:
    """Scheduler processes all enabled users and sends per-user notifications."""
    user_a = _create_user(db, ntfy_topic="topic-a")
    user_b = _create_user(db, ntfy_topic="topic-b")

    card_a = _create_card(db, user_a, alias="Card A", last4="1111")
    card_b = _create_card(db, user_b, alias="Card B", last4="2222")
    _create_statement(db, card_a, current_balance=Decimal("100.00"))
    _create_statement(db, card_b, current_balance=Decimal("200.00"))

    mock_ntfy = NtfyClient(server_url="https://ntfy.sh")
    mock_ntfy.send = AsyncMock(return_value=True)

    scheduler = NotificationScheduler(
        session_factory=_build_session_factory(db),
        ntfy_client_factory=lambda: mock_ntfy,
    )

    await scheduler._execute()

    assert mock_ntfy.send.call_count == 2
    topics_called = {call.kwargs["topic"] for call in mock_ntfy.send.call_args_list}
    assert topics_called == {"topic-a", "topic-b"}


@pytest.mark.asyncio
async def test_execute_with_no_enabled_users(db: Session) -> None:
    """Scheduler completes gracefully when no users have notifications on."""
    _create_user(db, notifications_enabled=False)

    mock_ntfy = NtfyClient(server_url="https://ntfy.sh")
    mock_ntfy.send = AsyncMock(return_value=True)

    scheduler = NotificationScheduler(
        session_factory=_build_session_factory(db),
        ntfy_client_factory=lambda: mock_ntfy,
    )

    await scheduler._execute()

    mock_ntfy.send.assert_not_called()


@pytest.mark.asyncio
async def test_execute_with_mixed_paid_and_unpaid(db: Session) -> None:
    """Only unpaid statements due tomorrow are included in notifications."""
    user = _create_user(db)
    card = _create_card(db, user)

    _create_statement(db, card, current_balance=Decimal("500.00"), is_fully_paid=False)
    _create_statement(db, card, current_balance=Decimal("300.00"), is_fully_paid=True)
    _create_statement(
        db,
        card,
        current_balance=Decimal("100.00"),
        due_date=date.today() + timedelta(days=5),
    )

    mock_ntfy = NtfyClient(server_url="https://ntfy.sh")
    mock_ntfy.send = AsyncMock(return_value=True)

    scheduler = NotificationScheduler(
        session_factory=_build_session_factory(db),
        ntfy_client_factory=lambda: mock_ntfy,
    )

    await scheduler._execute()

    mock_ntfy.send.assert_called_once()
    call_kwargs = mock_ntfy.send.call_args.kwargs
    assert "500.00" in call_kwargs["message"]


@pytest.mark.asyncio
async def test_execute_continues_after_ntfy_failure(db: Session) -> None:
    """A failed ntfy send for one user does not block processing others."""
    user_a = _create_user(db, ntfy_topic="topic-a")
    user_b = _create_user(db, ntfy_topic="topic-b")

    card_a = _create_card(db, user_a, last4="1111")
    card_b = _create_card(db, user_b, last4="2222")
    _create_statement(db, card_a)
    _create_statement(db, card_b)

    mock_ntfy = NtfyClient(server_url="https://ntfy.sh")
    # First call fails, second succeeds
    mock_ntfy.send = AsyncMock(side_effect=[False, True])

    scheduler = NotificationScheduler(
        session_factory=_build_session_factory(db),
        ntfy_client_factory=lambda: mock_ntfy,
    )

    await scheduler._execute()

    assert mock_ntfy.send.call_count == 2


# ---------------------------------------------------------------------------
# Scheduler lifecycle tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scheduler_start_stop_lifecycle() -> None:
    """Scheduler can start and stop cleanly without errors."""
    scheduler = NotificationScheduler(hour=23, minute=59)

    scheduler.start()
    assert scheduler._running is True
    assert scheduler._task is not None

    await scheduler.stop()
    assert scheduler._running is False
    assert scheduler._task is None


@pytest.mark.asyncio
async def test_scheduler_stop_is_idempotent() -> None:
    """Calling stop on an already-stopped scheduler is safe."""
    scheduler = NotificationScheduler()

    # Should not raise
    await scheduler.stop()
    assert scheduler._running is False


@pytest.mark.asyncio
async def test_scheduler_start_is_idempotent() -> None:
    """Calling start twice does not create duplicate tasks."""
    scheduler = NotificationScheduler(hour=23, minute=59)

    scheduler.start()
    first_task = scheduler._task

    scheduler.start()  # second call should be a no-op
    assert scheduler._task is first_task

    await scheduler.stop()
