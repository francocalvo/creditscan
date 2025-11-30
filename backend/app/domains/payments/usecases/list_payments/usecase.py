"""Usecase for listing payments."""

from __future__ import annotations

import uuid

from app.domains.payments.domain.models import PaymentsPublic
from app.domains.payments.service import PaymentService


class ListPaymentsUseCase:
    """Usecase for listing payments."""

    def __init__(self, service: PaymentService) -> None:
        """Initialize the usecase with a service."""
        self.service = service

    def execute(
        self, skip: int = 0, limit: int = 100, user_id: uuid.UUID | None = None
    ) -> PaymentsPublic:
        """Execute the usecase to list payments.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            user_id: Optional filter by user ID

        Returns:
            PaymentsPublic: Paginated list of payments
        """
        filters = {}
        if user_id:
            filters["user_id"] = user_id

        return self.service.list_payments(skip=skip, limit=limit, filters=filters)


def provide() -> ListPaymentsUseCase:
    """Provide an instance of ListPaymentsUseCase."""
    from app.domains.payments.service import provide as provide_service

    return ListPaymentsUseCase(provide_service())
