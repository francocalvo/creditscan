"""Usecase for creating a credit card."""

from sqlmodel import Session

from app.domains.credit_cards.domain.models import (
    CreditCardCreate,
    CreditCardPublic,
)
from app.domains.credit_cards.service import CreditCardService


class CreateCreditCardUseCase:
    """Usecase for creating a credit card."""

    def __init__(self, service: CreditCardService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(self, card_data: CreditCardCreate) -> CreditCardPublic:
        """Execute the usecase to create a credit card.

        Args:
            card_data: Credit card data to create

        Returns:
            CreditCardPublic: Created credit card data
        """
        return self.service.create_card(card_data)


def provide(session: Session) -> CreateCreditCardUseCase:
    """Provide an instance of CreateCreditCardUseCase.

    Args:
        session: The database session to use.
    """
    from app.domains.credit_cards.service import provide as provide_service

    return CreateCreditCardUseCase(provide_service(session))
