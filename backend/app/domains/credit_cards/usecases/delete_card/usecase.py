"""Usecase for deleting a credit card."""

import uuid

from sqlmodel import Session

from app.domains.credit_cards.service import CreditCardService


class DeleteCreditCardUseCase:
    """Usecase for deleting a credit card."""

    def __init__(self, service: CreditCardService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(self, card_id: uuid.UUID) -> None:
        """Execute the usecase to delete a credit card.

        Args:
            card_id: Credit card ID
        """
        self.service.delete_card(card_id)


def provide(session: Session) -> DeleteCreditCardUseCase:
    """Provide an instance of DeleteCreditCardUseCase.

    Args:
        session: The database session to use.
    """
    from app.domains.credit_cards.service import provide as provide_service

    return DeleteCreditCardUseCase(provide_service(session))
