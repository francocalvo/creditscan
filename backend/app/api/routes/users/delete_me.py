"""Delete current user endpoint."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser
from app.domains.users.domain.errors import InvalidUserDataError
from app.domains.users.usecases import provide_delete_user
from app.models import Message

router = APIRouter()


@router.delete("/me", response_model=Message)
def delete_current_user(current_user: CurrentUser) -> Any:
    """Delete own user."""
    try:
        usecase = provide_delete_user()
        usecase.execute(current_user.id, current_user.id)
        return Message(message="User deleted successfully")
    except InvalidUserDataError as e:
        raise HTTPException(status_code=403, detail=str(e))
