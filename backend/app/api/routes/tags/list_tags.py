"""List tags endpoint."""

import uuid
from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.domains.tags.domain.models import TagsPublic
from app.domains.tags.usecases.list_tags import provide as provide_list_tags

router = APIRouter()


@router.get("/", response_model=TagsPublic)
def list_tags(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    user_id: uuid.UUID | None = None,
) -> Any:
    """Retrieve tags.

    By default, returns the current user's tags. Superusers can filter by user_id.
    """
    usecase = provide_list_tags(session)

    # If user_id is not provided, use current user's ID
    # If user_id is provided but user is not superuser, only show their own tags
    filter_user_id = (
        user_id if (user_id and current_user.is_superuser) else current_user.id
    )

    return usecase.execute(skip=skip, limit=limit, user_id=filter_user_id)
