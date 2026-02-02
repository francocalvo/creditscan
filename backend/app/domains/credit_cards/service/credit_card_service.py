"""Credit card service implementation."""

import uuid
from typing import Any

from sqlmodel import Session

from app.domains.credit_cards.domain.models import (
    CreditCardCreate,
    CreditCardPublic,
    CreditCardsPublic,
    CreditCardUpdate,
)
from app.domains.credit_cards.repository.credit_card_repository import (
    CreditCardRepository,
)


class CreditCardService:
    """Service for credit cards."""

    def __init__(self, repository: CreditCardRepository):
        """Initialize the service with a repository."""
        self.repository = repository

    def create_card(self, card_data: CreditCardCreate) -> CreditCardPublic:
        """Create a new credit card."""
        card = self.repository.create(card_data)
        return CreditCardPublic.model_validate(card)

    def get_card(self, card_id: uuid.UUID) -> CreditCardPublic:
        """Get a credit card by ID."""
        card = self.repository.get_by_id(card_id)
        return CreditCardPublic.model_validate(card)

    def list_cards(
        self, skip: int = 0, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> CreditCardsPublic:
        """List credit cards with pagination and filtering."""
        cards = self.repository.list(skip=skip, limit=limit, filters=filters)
        count = self.repository.count(filters=filters)

        return CreditCardsPublic(
            data=[CreditCardPublic.model_validate(c) for c in cards],
            count=count,
        )

    def update_card(
        self, card_id: uuid.UUID, card_data: CreditCardUpdate
    ) -> CreditCardPublic:
        """Update a credit card."""
        card = self.repository.update(card_id, card_data)
        return CreditCardPublic.model_validate(card)

    def delete_card(self, card_id: uuid.UUID) -> None:
        """Delete a credit card."""
        self.repository.delete(card_id)


def provide(session: Session) -> CreditCardService:
    """Provide an instance of CreditCardService.

    Args:
        session: The database session to use.
    """
    from app.domains.credit_cards.repository import provide as provide_repository

    return CreditCardService(provide_repository(session))
