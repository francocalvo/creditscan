"""Delete tag endpoint."""

import uuid

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.domains.tags.domain.errors import TagNotFoundError
from app.domains.tags.usecases.delete_tag import provide as provide_delete_tag
from app.domains.tags.usecases.get_tag import provide as provide_get_tag

router = APIRouter()


@router.delete("/{tag_id}", status_code=204)
def delete_tag(
    session: SessionDep,
    tag_id: uuid.UUID,
    current_user: CurrentUser,
) -> None:
    """Delete a tag.

    Users can only delete their own tags.
    Superusers can delete any tag.
    """
    try:
        # First, check if the tag exists and belongs to the user
        get_usecase = provide_get_tag(session)
        existing_tag = get_usecase.execute(tag_id)

        if existing_tag.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to delete this tag",
            )

        # Delete the tag
        delete_usecase = provide_delete_tag(session)
        delete_usecase.execute(tag_id)
    except TagNotFoundError:
        raise HTTPException(status_code=404, detail="Tag not found")
