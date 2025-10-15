"""List users endpoint."""

from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import get_current_active_superuser
from app.domains.users.domain.models import UsersPublic
from app.domains.users.usecases import provide_list_users

router = APIRouter()


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
def list_users(skip: int = 0, limit: int = 100) -> Any:
    """Retrieve users."""
    usecase = provide_list_users()
    return usecase.execute(skip=skip, limit=limit)
