"""Usecase for listing credit cards."""

import uuid

from sqlmodel import Session

from app.domains.credit_cards.domain.models import CreditCardsPublic
from app.domains.credit_cards.service import CreditCardService


class ListCreditCardsUseCase:
    """Usecase for listing credit cards with pagination."""

    def __init__(self, service: CreditCardService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(
        self, skip: int = 0, limit: int = 100, user_id: uuid.UUID | None = None
    ) -> CreditCardsPublic:
        """Execute the usecase to list credit cards.

        Args:
            skip: Number of records to skip
            limit: Number of records to return
            user_id: Optional filter by user ID

        Returns:
            CreditCardsPublic: Paginated cards data
        """
        filters = {}
        if user_id:
            filters["user_id"] = user_id

        return self.service.list_cards(skip=skip, limit=limit, filters=filters)


def provide(session: Session) -> ListCreditCardsUseCase:
    """Provide an instance of ListCreditCardsUseCase.

    Args:
        session: The database session to use.
    """
    from app.domains.credit_cards.service import provide as provide_service

    return ListCreditCardsUseCase(provide_service(session))
