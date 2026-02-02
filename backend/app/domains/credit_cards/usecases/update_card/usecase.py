"""Usecase for updating a credit card."""

import uuid

from sqlmodel import Session

from app.domains.credit_cards.domain.models import (
    CreditCardPublic,
    CreditCardUpdate,
)
from app.domains.credit_cards.service import CreditCardService


class UpdateCreditCardUseCase:
    """Usecase for updating a credit card."""

    def __init__(self, service: CreditCardService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(
        self, card_id: uuid.UUID, card_data: CreditCardUpdate
    ) -> CreditCardPublic:
        """Execute the usecase to update a credit card.

        Args:
            card_id: Credit card ID
            card_data: Credit card data to update

        Returns:
            CreditCardPublic: Updated credit card data
        """
        return self.service.update_card(card_id, card_data)


def provide(session: Session) -> UpdateCreditCardUseCase:
    """Provide an instance of UpdateCreditCardUseCase.

    Args:
        session: The database session to use.
    """
    from app.domains.credit_cards.service import provide as provide_service

    return UpdateCreditCardUseCase(provide_service(session))
