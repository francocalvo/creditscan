"""Update current user endpoint."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.domains.users.domain.errors import DuplicateUserError
from app.domains.users.domain.models import UserPublic, UserUpdateMe
from app.domains.users.usecases.update_user import provide as provide_update_user

router = APIRouter()


@router.patch("/me", response_model=UserPublic)
def update_current_user(
    session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """Update own user."""
    try:
        usecase = provide_update_user(session)
        return usecase.execute(current_user.id, user_in)
    except DuplicateUserError as e:
        raise HTTPException(status_code=409, detail=str(e))
