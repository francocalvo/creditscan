"""Update tag endpoint."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser
from app.domains.tags.domain.errors import InvalidTagDataError, TagNotFoundError
from app.domains.tags.domain.models import TagPublic, TagUpdate
from app.domains.tags.usecases.get_tag import provide as provide_get_tag
from app.domains.tags.usecases.update_tag import provide as provide_update_tag

router = APIRouter()


@router.patch("/{tag_id}", response_model=TagPublic)
def update_tag(
    tag_id: uuid.UUID,
    tag_in: TagUpdate,
    current_user: CurrentUser,
) -> Any:
    """Update a tag.

    Users can only update their own tags.
    Superusers can update any tag.
    """
    try:
        # First, check if the tag exists and belongs to the user
        get_usecase = provide_get_tag()
        existing_tag = get_usecase.execute(tag_id)

        if existing_tag.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to update this tag",
            )

        # Update the tag
        update_usecase = provide_update_tag()
        return update_usecase.execute(tag_id, tag_in)
    except TagNotFoundError:
        raise HTTPException(status_code=404, detail="Tag not found")
    except InvalidTagDataError as e:
        raise HTTPException(status_code=400, detail=str(e))
