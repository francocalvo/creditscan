"""Delete user by ID endpoint."""

import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import CurrentUser, get_current_active_superuser
from app.domains.users.domain.errors import InvalidUserDataError, UserNotFoundError
from app.domains.users.usecases import provide_delete_user
from app.models import Message

router = APIRouter()


@router.delete(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=Message,
)
def delete_user_by_id(user_id: uuid.UUID, current_user: CurrentUser) -> Message:
    """Delete a user."""
    try:
        usecase = provide_delete_user()
        usecase.execute(user_id, current_user.id)
        return Message(message="User deleted successfully")
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except InvalidUserDataError as e:
        raise HTTPException(status_code=403, detail=str(e))
