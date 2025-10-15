"""List card statements endpoint."""

import uuid
from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.domains.card_statements.domain.models import CardStatementsPublic
from app.domains.card_statements.usecases import provide_list_statements

router = APIRouter()


@router.get("/", response_model=CardStatementsPublic)
def list_card_statements(
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    user_id: uuid.UUID | None = None,
    card_last4: str | None = None,
) -> Any:
    """Retrieve card statements.

    By default, returns the current user's statements. Superusers can filter by user_id.
    """
    usecase = provide_list_statements()

    # If user_id is not provided, use current user's ID
    # If user_id is provided but user is not superuser, only show their own statements
    filter_user_id = (
        user_id if (user_id and current_user.is_superuser) else current_user.id
    )

    return usecase.execute(
        skip=skip,
        limit=limit,
        user_id=filter_user_id,
        card_last4=card_last4,
    )
