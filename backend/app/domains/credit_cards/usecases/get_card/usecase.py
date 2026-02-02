"""Usecase for getting a credit card by ID."""

import uuid

from sqlmodel import Session

from app.domains.credit_cards.domain.models import CreditCardPublic
from app.domains.credit_cards.service import CreditCardService


class GetCreditCardUseCase:
    """Usecase for getting a credit card by ID."""

    def __init__(self, service: CreditCardService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(self, card_id: uuid.UUID) -> CreditCardPublic:
        """Execute the usecase to get a credit card.

        Args:
            card_id: Credit card ID

        Returns:
            CreditCardPublic: Credit card data
        """
        return self.service.get_card(card_id)


def provide(session: Session) -> GetCreditCardUseCase:
    """Provide an instance of GetCreditCardUseCase.

    Args:
        session: The database session to use.
    """
    from app.domains.credit_cards.service import provide as provide_service

    return GetCreditCardUseCase(provide_service(session))
