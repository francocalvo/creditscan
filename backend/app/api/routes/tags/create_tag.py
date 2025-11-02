"""Create tag endpoint."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser
from app.domains.tags.domain.errors import InvalidTagDataError
from app.domains.tags.domain.models import TagCreate, TagPublic
from app.domains.tags.usecases.create_tag import provide as provide_create_tag

router = APIRouter()


@router.post("/", response_model=TagPublic, status_code=201)
def create_tag(
    tag_in: TagCreate,
    current_user: CurrentUser,
) -> Any:
    """Create a new tag.

    Users can only create tags for themselves.
    Superusers can create tags for any user.
    """
    # Ensure users can only create tags for themselves
    if not current_user.is_superuser and tag_in.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only create tags for yourself",
        )

    try:
        usecase = provide_create_tag()
        return usecase.execute(tag_in)
    except InvalidTagDataError as e:
        raise HTTPException(status_code=400, detail=str(e))
