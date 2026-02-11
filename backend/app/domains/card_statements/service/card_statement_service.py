"""Card statement service implementation."""

import uuid
from decimal import Decimal
from typing import Any

from sqlmodel import Session

from app.domains.card_statements.domain.models import (
    CardStatementCreate,
    CardStatementPublic,
    CardStatementsPublic,
    CardStatementUpdate,
)
from app.domains.card_statements.repository import provide as provide_repository
from app.domains.card_statements.repository.card_statement_repository import (
    CardStatementRepository,
)
from app.domains.payments.repository.payment_repository import PaymentRepository


class CardStatementService:
    """Service for card statements."""

    def __init__(
        self,
        repository: CardStatementRepository,
        payment_repository: PaymentRepository,
    ):
        """Initialize the service with a repository."""
        self.repository = repository
        self.payment_repository = payment_repository

    def create_statement(
        self, statement_data: CardStatementCreate
    ) -> CardStatementPublic:
        """Create a new card statement."""
        statement = self.repository.create(statement_data)
        return CardStatementPublic.model_validate(statement)

    def get_statement(self, statement_id: uuid.UUID) -> CardStatementPublic:
        """Get a card statement by ID."""
        statement = self.repository.get_by_id(statement_id)
        pub = CardStatementPublic.model_validate(statement)
        pub.total_paid = self.payment_repository.get_sum_by_statement_id(statement_id)
        return pub

    def list_statements(
        self, skip: int = 0, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> CardStatementsPublic:
        """List card statements with pagination and filtering."""
        statements = self.repository.list(skip=skip, limit=limit, filters=filters)
        count = self.repository.count(filters=filters)

        pub_list = [CardStatementPublic.model_validate(s) for s in statements]

        statement_ids = [s.id for s in pub_list]
        sums = self.payment_repository.get_sums_by_statement_ids(statement_ids)
        for pub in pub_list:
            pub.total_paid = sums.get(pub.id, Decimal("0"))

        return CardStatementsPublic(
            data=pub_list,
            count=count,
        )

    def update_statement(
        self, statement_id: uuid.UUID, statement_data: CardStatementUpdate
    ) -> CardStatementPublic:
        """Update a card statement."""
        statement = self.repository.update(statement_id, statement_data)
        pub = CardStatementPublic.model_validate(statement)
        pub.total_paid = self.payment_repository.get_sum_by_statement_id(statement_id)
        return pub

    def delete_statement(self, statement_id: uuid.UUID) -> None:
        """Delete a card statement."""
        self.repository.delete(statement_id)


def provide(session: Session) -> CardStatementService:
    """Provide an instance of CardStatementService.

    Args:
        session: The database session to use.
    """
    return CardStatementService(
        provide_repository(session),
        PaymentRepository(session),
    )
