"""Payment service implementation."""

from __future__ import annotations

import uuid
from typing import Any

from sqlmodel import Session

from app.domains.card_statements.domain.models import CardStatementUpdate
from app.domains.card_statements.repository.card_statement_repository import (
    CardStatementRepository,
)
from app.domains.payments.domain.models import (
    PaymentCreate,
    PaymentPublic,
    PaymentsPublic,
    PaymentUpdate,
)
from app.domains.payments.repository.payment_repository import PaymentRepository


class PaymentService:
    """Service for payments."""

    def __init__(
        self,
        repository: PaymentRepository,
        card_statement_repository: CardStatementRepository,
    ):
        """Initialize the service with a repository."""
        self.repository = repository
        self.card_statement_repository = card_statement_repository

    def _update_statement_payment_status(self, statement_id: uuid.UUID) -> None:
        """Check and update the is_fully_paid flag for a statement.

        Compares the sum of all payments for the statement with the current_balance.
        Sets is_fully_paid to True if the sum >= current_balance.

        Args:
            statement_id: The statement ID to check and update
        """
        statement = self.card_statement_repository.get_by_id(statement_id)

        # Get the sum of all payments for this statement
        total_payments = self.repository.get_sum_by_statement_id(statement_id)

        # Check if payments exceed or equal the current balance
        # If current_balance is None, we can't determine if it's paid
        is_fully_paid = False
        if statement.current_balance is not None:
            is_fully_paid = total_payments >= statement.current_balance

        # Only update if the value has changed
        if statement.is_fully_paid != is_fully_paid:
            update_data = CardStatementUpdate(is_fully_paid=is_fully_paid)
            self.card_statement_repository.update(statement_id, update_data)

    def create_payment(self, payment_data: PaymentCreate) -> PaymentPublic:
        """Create a new payment."""
        payment = self.repository.create(payment_data)
        # Update the statement's is_fully_paid flag
        self._update_statement_payment_status(payment.statement_id)
        return PaymentPublic.model_validate(payment)

    def get_payment(self, payment_id: uuid.UUID) -> PaymentPublic:
        """Get a payment by ID."""
        payment = self.repository.get_by_id(payment_id)
        return PaymentPublic.model_validate(payment)

    def list_payments(
        self, skip: int = 0, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> PaymentsPublic:
        """List payments with pagination and filtering."""
        payments = self.repository.list(skip=skip, limit=limit, filters=filters)
        count = self.repository.count(filters=filters)

        return PaymentsPublic(
            data=[PaymentPublic.model_validate(p) for p in payments],
            count=count,
            pagination={"skip": skip, "limit": limit},
        )

    def update_payment(
        self, payment_id: uuid.UUID, payment_data: PaymentUpdate
    ) -> PaymentPublic:
        """Update a payment."""
        # Get the payment before updating to know the old statement_id
        old_payment = self.repository.get_by_id(payment_id)
        old_statement_id = old_payment.statement_id

        payment = self.repository.update(payment_id, payment_data)
        new_statement_id = payment.statement_id

        # Update the payment status for both old and new statements
        # (in case the statement_id changed)
        self._update_statement_payment_status(new_statement_id)
        if old_statement_id != new_statement_id:
            self._update_statement_payment_status(old_statement_id)

        return PaymentPublic.model_validate(payment)

    def delete_payment(self, payment_id: uuid.UUID) -> None:
        """Delete a payment."""
        # Get the payment before deleting to know the statement_id
        payment = self.repository.get_by_id(payment_id)
        statement_id = payment.statement_id

        self.repository.delete(payment_id)
        # Update the statement's is_fully_paid flag
        self._update_statement_payment_status(statement_id)


def provide(session: Session) -> PaymentService:
    """Provide an instance of PaymentService.

    Args:
        session: The database session to use.
    """
    from app.domains.card_statements.repository import (
        provide as provide_card_statement_repository,
    )
    from app.domains.payments.repository import provide as provide_repository

    return PaymentService(
        provide_repository(session), provide_card_statement_repository(session)
    )
