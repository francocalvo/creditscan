"""User signup endpoint."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import SessionDep
from app.core.config import settings
from app.domains.users.domain.errors import DuplicateUserError
from app.domains.users.domain.models import UserPublic, UserRegister
from app.domains.users.usecases.register_user import provide as provide_register_user

router = APIRouter()


@router.post("/signup", response_model=UserPublic)
def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """Create new user without the need to be logged in."""
    if not settings.USERS_OPEN_REGISTRATION:
        raise HTTPException(status_code=403, detail="Signups are currently disabled.")
    try:
        usecase = provide_register_user(session)
        return usecase.execute(user_in)
    except DuplicateUserError as e:
        raise HTTPException(status_code=400, detail=str(e))
