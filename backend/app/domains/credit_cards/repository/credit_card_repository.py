"""Credit card repository implementation."""

import uuid
from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from sqlmodel import Session, func, select

from app.domains.card_statements.domain.models import CardStatement
from app.domains.credit_cards.domain.errors import CreditCardNotFoundError
from app.domains.credit_cards.domain.models import (
    CreditCard,
    CreditCardCreate,
    CreditCardUpdate,
)


class CreditCardRepository:
    """Repository for credit cards."""

    def __init__(self, db_session: Session):
        """Initialize the repository with a database session."""
        self.db_session = db_session

    def create(self, card_data: CreditCardCreate) -> CreditCard:
        """Create a new credit card."""
        card = CreditCard.model_validate(card_data)
        self.db_session.add(card)
        self.db_session.commit()
        self.db_session.refresh(card)
        return card

    def get_by_id(self, card_id: uuid.UUID) -> CreditCard:
        """Get a credit card by ID."""
        card = self.db_session.get(CreditCard, card_id)
        if not card:
            raise CreditCardNotFoundError(f"Credit card with ID {card_id} not found")
        return card

    def list(
        self, skip: int = 0, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> list[CreditCard]:
        """List credit cards with pagination and filtering."""
        query = select(CreditCard)

        if filters:
            for field, value in filters.items():
                if hasattr(CreditCard, field):
                    query = query.where(getattr(CreditCard, field) == value)

        result = self.db_session.exec(query.offset(skip).limit(limit))
        return list(result)

    def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count credit cards with optional filtering."""
        query = select(CreditCard)

        if filters:
            for field, value in filters.items():
                if hasattr(CreditCard, field):
                    query = query.where(getattr(CreditCard, field) == value)

        count_q = (
            query.with_only_columns(func.count())
            .order_by(None)
            .select_from(query.get_final_froms()[0])
        )

        result = self.db_session.exec(count_q)
        for count in result:
            return count  # type: ignore
        return 0

    def update(
        self, card_id: uuid.UUID, card_data: CreditCardUpdate, **kwargs: Any
    ) -> CreditCard:
        """Update a credit card."""
        card = self.get_by_id(card_id)

        update_dict = card_data.model_dump(exclude_unset=True)
        update_dict.update(kwargs)
        for field, value in update_dict.items():
            setattr(card, field, value)

        self.db_session.add(card)
        self.db_session.commit()
        self.db_session.refresh(card)
        return card

    def delete(self, card_id: uuid.UUID) -> None:
        """Delete a credit card."""
        card = self.get_by_id(card_id)
        self.db_session.delete(card)
        self.db_session.commit()

    def get_outstanding_balance(self, card_id: uuid.UUID) -> Decimal:
        """Calculate the outstanding balance for a credit card.

        The outstanding balance is the sum of current_balance from all unpaid statements.
        """
        query = select(func.coalesce(func.sum(CardStatement.current_balance), 0)).where(
            CardStatement.card_id == card_id,
            CardStatement.is_fully_paid.is_(False),
        )
        result = self.db_session.exec(query).first()
        return Decimal(result or 0)

    def get_outstanding_balances(
        self, card_ids: Sequence[uuid.UUID]
    ) -> dict[uuid.UUID, Decimal]:
        """Calculate the outstanding balance for multiple credit cards.

        Returns a dictionary mapping card_id to outstanding_balance.
        """
        if not card_ids:
            return {}

        query = (
            select(
                CardStatement.card_id,
                func.coalesce(func.sum(CardStatement.current_balance), 0),
            )
            .where(
                CardStatement.card_id.in_(card_ids),
                CardStatement.is_fully_paid.is_(False),
            )
            .group_by(CardStatement.card_id)
        )
        results = self.db_session.exec(query).all()

        balances = {card_id: Decimal(0) for card_id in card_ids}
        for card_id, balance in results:
            balances[card_id] = Decimal(balance or 0)

        return balances


def provide(session: Session) -> CreditCardRepository:
    """Provide an instance of CreditCardRepository.

    Args:
        session: The database session to use.

    Returns:
        CreditCardRepository: An instance of CreditCardRepository with the given session.
    """
    return CreditCardRepository(session)
