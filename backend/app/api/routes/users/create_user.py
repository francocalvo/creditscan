"""Create user endpoint."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import SessionDep, get_current_active_superuser
from app.domains.users.domain.errors import DuplicateUserError
from app.domains.users.domain.models import UserCreate, UserPublic
from app.domains.users.usecases.create_user import provide as provide_create_user

router = APIRouter()


@router.post(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
def create_user(session: SessionDep, user_in: UserCreate) -> Any:
    """Create new user."""
    try:
        usecase = provide_create_user(session)
        return usecase.execute(user_in, send_welcome_email=True)
    except DuplicateUserError as e:
        raise HTTPException(status_code=400, detail=str(e))
