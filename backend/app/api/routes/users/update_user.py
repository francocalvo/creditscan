"""Update user by ID endpoint."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_active_superuser
from app.domains.users.domain.errors import DuplicateUserError, UserNotFoundError
from app.domains.users.domain.models import UserPublic, UserUpdate
from app.domains.users.usecases import provide_update_user

router = APIRouter()


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
def update_user_by_id(user_id: uuid.UUID, user_in: UserUpdate) -> Any:
    """Update a user."""
    try:
        usecase = provide_update_user()
        return usecase.execute(user_id, user_in)
    except UserNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    except DuplicateUserError as e:
        raise HTTPException(status_code=409, detail=str(e))
