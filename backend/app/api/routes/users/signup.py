"""User signup endpoint."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.domains.users.domain.errors import DuplicateUserError
from app.domains.users.domain.models import UserPublic, UserRegister
from app.domains.users.usecases import provide_register_user

router = APIRouter()


@router.post("/signup", response_model=UserPublic)
def register_user(user_in: UserRegister) -> Any:
    """Create new user without the need to be logged in."""
    try:
        usecase = provide_register_user()
        return usecase.execute(user_in)
    except DuplicateUserError as e:
        raise HTTPException(status_code=400, detail=str(e))
