"""Usecase for updating a payment."""

from __future__ import annotations

import uuid

from app.domains.payments.domain.models import PaymentPublic, PaymentUpdate
from app.domains.payments.service import PaymentService


class UpdatePaymentUseCase:
    """Usecase for updating a payment."""

    def __init__(self, service: PaymentService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(
        self, payment_id: uuid.UUID, payment_data: PaymentUpdate
    ) -> PaymentPublic:
        """Execute the usecase to update a payment.

        Args:
            payment_id: Payment ID to update
            payment_data: Updated payment data

        Returns:
            PaymentPublic: Updated payment data
        """
        return self.service.update_payment(payment_id, payment_data)


def provide() -> UpdatePaymentUseCase:
    """Provide an instance of UpdatePaymentUseCase."""
    from app.domains.payments.service import provide as provide_service

    return UpdatePaymentUseCase(provide_service())
