"""Usecase for listing card statements."""

import uuid

from app.domains.card_statements.domain.models import CardStatementsPublic
from app.domains.card_statements.service import CardStatementService
from app.domains.card_statements.service import provide as provide_service


class ListCardStatementsUseCase:
    """Usecase for listing card statements with pagination."""

    def __init__(self, service: CardStatementService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: uuid.UUID | None = None,
        card_id: uuid.UUID | None = None,
    ) -> CardStatementsPublic:
        """Execute the usecase to list card statements.

        Args:
            skip: Number of records to skip
            limit: Number of records to return
            user_id: Optional filter by user ID (via credit card relationship)
            card_id: Optional filter by card ID

        Returns:
            CardStatementsPublic: Paginated statements data
        """
        filters = {}
        if user_id:
            filters["user_id"] = user_id
        if card_id:
            filters["card_id"] = card_id

        return self.service.list_statements(skip=skip, limit=limit, filters=filters)


def provide() -> ListCardStatementsUseCase:
    """Provide an instance of ListCardStatementsUseCase."""
    return ListCardStatementsUseCase(provide_service())
