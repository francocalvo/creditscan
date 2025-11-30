"""List credit cards endpoint."""

import uuid
from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.domains.credit_cards.domain.models import CreditCardsPublic
from app.domains.credit_cards.usecases.list_cards import provide

router = APIRouter()


@router.get("/", response_model=CreditCardsPublic)
def list_credit_cards(
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    user_id: uuid.UUID | None = None,
) -> Any:
    """Retrieve credit cards.

    By default, returns the current user's cards. Superusers can filter by user_id.
    """
    usecase = provide()

    # If user_id is not provided, use current user's ID
    # If user_id is provided but user is not superuser, only show their own cards
    filter_user_id = (
        user_id if (user_id and current_user.is_superuser) else current_user.id
    )

    return usecase.execute(
        skip=skip,
        limit=limit,
        user_id=filter_user_id,
    )
