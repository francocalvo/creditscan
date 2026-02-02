"""Update current user password endpoint."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.domains.users.domain.errors import (
    InvalidCredentialsError,
    InvalidUserDataError,
)
from app.domains.users.domain.models import UpdatePassword
from app.domains.users.usecases.update_password import (
    provide as provide_update_password,
)
from app.models import Message

router = APIRouter()


@router.patch("/me/password", response_model=Message)
def update_current_user_password(
    session: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """Update own password."""
    try:
        usecase = provide_update_password(session)
        usecase.execute(current_user.id, body)
        return Message(message="Password updated successfully")
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidUserDataError as e:
        raise HTTPException(status_code=400, detail=str(e))
