"""Usecase for getting a payment."""

from __future__ import annotations

import uuid

from app.domains.payments.domain.models import PaymentPublic
from app.domains.payments.service import PaymentService


class GetPaymentUseCase:
    """Usecase for getting a payment."""

    def __init__(self, service: PaymentService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(self, payment_id: uuid.UUID) -> PaymentPublic:
        """Execute the usecase to get a payment.

        Args:
            payment_id: Payment ID to retrieve

        Returns:
            PaymentPublic: Payment data
        """
        return self.service.get_payment(payment_id)


def provide() -> GetPaymentUseCase:
    """Provide an instance of GetPaymentUseCase."""
    from app.domains.payments.service import provide as provide_service

    return GetPaymentUseCase(provide_service())
