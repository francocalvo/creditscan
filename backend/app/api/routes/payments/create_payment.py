"""Create payment endpoint."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser
from app.domains.payments.domain.models import PaymentCreate, PaymentPublic
from app.domains.payments.usecases.create_payment import provide

router = APIRouter()


@router.post("/", response_model=PaymentPublic, status_code=201)
def create_payment(
    payment_in: PaymentCreate,
    current_user: CurrentUser,
) -> Any:
    """Create a new payment.

    Users can only create payments for themselves.
    Superusers can create payments for any user.
    """
    # Ensure users can only create payments for themselves
    if not current_user.is_superuser and payment_in.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only create payments for yourself",
        )

    usecase = provide()
    return usecase.execute(payment_in)
