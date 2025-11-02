"""Get tag by ID endpoint."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser
from app.domains.tags.domain.errors import TagNotFoundError
from app.domains.tags.domain.models import TagPublic
from app.domains.tags.usecases.get_tag import provide as provide_get_tag

router = APIRouter()


@router.get("/{tag_id}", response_model=TagPublic)
def get_tag(tag_id: uuid.UUID, current_user: CurrentUser) -> Any:
    """Get a specific tag by ID.

    Users can only view their own tags.
    Superusers can view any tag.
    """
    try:
        usecase = provide_get_tag()
        tag = usecase.execute(tag_id)

        # Allow users to see their own tags, or superusers to see any tag
        if tag.user_id == current_user.id or current_user.is_superuser:
            return tag

        raise HTTPException(
            status_code=403,
            detail="You don't have permission to view this tag",
        )
    except TagNotFoundError:
        raise HTTPException(status_code=404, detail="Tag not found")
