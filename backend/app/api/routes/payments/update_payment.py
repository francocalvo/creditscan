"""Update payment endpoint."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser
from app.domains.payments.domain.errors import PaymentNotFoundError
from app.domains.payments.domain.models import PaymentPublic, PaymentUpdate
from app.domains.payments.usecases.get_payment import provide as provide_get
from app.domains.payments.usecases.update_payment import provide

router = APIRouter()


@router.patch("/{payment_id}", response_model=PaymentPublic)
def update_payment(
    payment_id: uuid.UUID,
    payment_in: PaymentUpdate,
    current_user: CurrentUser,
) -> Any:
    """Update a payment.

    Users can only update their own payments.
    Superusers can update any payment.
    """
    try:
        # First, check if payment exists and user has permission
        get_usecase = provide_get()
        existing_payment = get_usecase.execute(payment_id)

        if (
            not current_user.is_superuser
            and existing_payment.user_id != current_user.id
        ):
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to update this payment",
            )

        usecase = provide()
        return usecase.execute(payment_id, payment_in)
    except PaymentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
