"""Delete payment endpoint."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser
from app.domains.payments.domain.errors import PaymentNotFoundError
from app.domains.payments.usecases.delete_payment import provide
from app.domains.payments.usecases.get_payment import provide as provide_get
from app.models import Message

router = APIRouter()


@router.delete("/{payment_id}", response_model=Message)
def delete_payment(
    payment_id: uuid.UUID,
    current_user: CurrentUser,
) -> Any:
    """Delete a payment.

    Users can only delete their own payments.
    Superusers can delete any payment.
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
                detail="You don't have permission to delete this payment",
            )

        usecase = provide()
        usecase.execute(payment_id)
        return Message(message="Payment deleted successfully")
    except PaymentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
