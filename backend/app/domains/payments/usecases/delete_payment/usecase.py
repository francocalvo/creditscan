"""Usecase for deleting a payment."""

from __future__ import annotations

import uuid

from sqlmodel import Session

from app.domains.payments.service import PaymentService


class DeletePaymentUseCase:
    """Usecase for deleting a payment."""

    def __init__(self, service: PaymentService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(self, payment_id: uuid.UUID) -> None:
        """Execute the usecase to delete a payment.

        Args:
            payment_id: Payment ID to delete
        """
        self.service.delete_payment(payment_id)


def provide(session: Session) -> DeletePaymentUseCase:
    """Provide an instance of DeletePaymentUseCase.

    Args:
        session: The database session to use.
    """
    from app.domains.payments.service import provide as provide_service

    return DeletePaymentUseCase(provide_service(session))
