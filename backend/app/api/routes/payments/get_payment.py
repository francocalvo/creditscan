"""Get payment endpoint."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.domains.payments.domain.errors import PaymentNotFoundError
from app.domains.payments.domain.models import PaymentPublic
from app.domains.payments.usecases.get_payment import provide

router = APIRouter()


@router.get("/{payment_id}", response_model=PaymentPublic)
def get_payment(
    session: SessionDep,
    payment_id: uuid.UUID,
    current_user: CurrentUser,
) -> Any:
    """Get a specific payment by ID.

    Users can only view their own payments.
    Superusers can view any payment.
    """
    try:
        usecase = provide(session)
        payment = usecase.execute(payment_id)

        # Check if user has permission to view this payment
        if not current_user.is_superuser and payment.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to view this payment",
            )

        return payment
    except PaymentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
