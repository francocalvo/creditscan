"""List payments endpoint."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.domains.payments.domain.models import PaymentsPublic
from app.domains.payments.usecases.list_payments import provide

router = APIRouter()


@router.get("/", response_model=PaymentsPublic)
def list_payments(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    user_id: uuid.UUID | None = None,
) -> Any:
    """Retrieve payments.

    By default, returns the current user's payments. Superusers can filter by user_id.
    """
    usecase = provide(session)

    # If user_id is not provided, use current user's ID
    # If user_id is provided but user is not superuser, only show their own payments
    filter_user_id = (
        user_id if (user_id and current_user.is_superuser) else current_user.id
    )

    return usecase.execute(
        skip=skip,
        limit=limit,
        user_id=filter_user_id,
    )
