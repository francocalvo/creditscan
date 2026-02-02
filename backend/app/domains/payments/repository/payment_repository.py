"""Payment repository implementation."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlmodel import Session, func, select

from app.domains.payments.domain.errors import PaymentNotFoundError
from app.domains.payments.domain.models import (
    Payment,
    PaymentCreate,
    PaymentUpdate,
)


class PaymentRepository:
    """Repository for payments."""

    def __init__(self, db_session: Session):
        """Initialize the repository with a database session."""
        self.db_session = db_session

    def create(self, payment_data: PaymentCreate) -> Payment:
        """Create a new payment."""
        payment = Payment.model_validate(payment_data)
        self.db_session.add(payment)
        self.db_session.commit()
        self.db_session.refresh(payment)
        return payment

    def get_by_id(self, payment_id: uuid.UUID) -> Payment:
        """Get a payment by ID."""
        payment = self.db_session.get(Payment, payment_id)
        if not payment:
            raise PaymentNotFoundError(f"Payment with ID {payment_id} not found")
        return payment

    def list(
        self, skip: int = 0, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> list[Payment]:
        """List payments with pagination and filtering."""
        query = select(Payment)

        if filters:
            for field, value in filters.items():
                if hasattr(Payment, field):
                    query = query.where(getattr(Payment, field) == value)

        result = self.db_session.exec(query.offset(skip).limit(limit))
        return list(result)

    def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count payments with optional filtering."""
        query = select(Payment)

        if filters:
            for field, value in filters.items():
                if hasattr(Payment, field):
                    query = query.where(getattr(Payment, field) == value)

        count_q = (
            query.with_only_columns(func.count())
            .order_by(None)
            .select_from(query.get_final_froms()[0])
        )

        result = self.db_session.exec(count_q)
        for count in result:
            return count  # type: ignore
        return 0

    def update(self, payment_id: uuid.UUID, payment_data: PaymentUpdate) -> Payment:
        """Update a payment."""
        payment = self.get_by_id(payment_id)

        update_dict = payment_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(payment, field, value)

        self.db_session.add(payment)
        self.db_session.commit()
        self.db_session.refresh(payment)
        return payment

    def delete(self, payment_id: uuid.UUID) -> None:
        """Delete a payment."""
        payment = self.get_by_id(payment_id)
        self.db_session.delete(payment)
        self.db_session.commit()

    def get_sum_by_statement_id(self, statement_id: uuid.UUID) -> Decimal:
        """Get the sum of all payments for a statement."""
        query = select(func.sum(Payment.amount)).where(
            Payment.statement_id == statement_id
        )
        result = self.db_session.exec(query)
        total = result.one()
        return total if total is not None else Decimal("0")


def provide(session: Session) -> PaymentRepository:
    """Provide an instance of PaymentRepository.

    Args:
        session: The database session to use.

    Returns:
        PaymentRepository: An instance of PaymentRepository with the given session.
    """
    return PaymentRepository(session)
