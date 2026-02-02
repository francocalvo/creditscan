"""Usecase for creating a payment."""

from __future__ import annotations

from sqlmodel import Session

from app.domains.payments.domain.models import PaymentCreate, PaymentPublic
from app.domains.payments.service import PaymentService


class CreatePaymentUseCase:
    """Usecase for creating a payment."""

    def __init__(self, service: PaymentService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(self, payment_data: PaymentCreate) -> PaymentPublic:
        """Execute the usecase to create a payment.

        Args:
            payment_data: Payment data to create

        Returns:
            PaymentPublic: Created payment data
        """
        return self.service.create_payment(payment_data)


def provide(session: Session) -> CreatePaymentUseCase:
    """Provide an instance of CreatePaymentUseCase.

    Args:
        session: The database session to use.
    """
    from app.domains.payments.service import provide as provide_service

    return CreatePaymentUseCase(provide_service(session))
