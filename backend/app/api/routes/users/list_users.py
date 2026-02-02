"""List users endpoint."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.domains.users.domain.models import UsersPublic
from app.domains.users.usecases.search_users import provide as provide_search_users

router = APIRouter()


@router.get("/", response_model=UsersPublic)
def list_users(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List all users (superusers only).

    Args:
        session: Database session
        current_user: Current authenticated user
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return

    Returns:
        UsersPublic: Paginated list of users with total count

    Raises:
        HTTPException: If user is not a superuser (403)
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )

    usecase = provide_search_users(session)
    return usecase.execute(skip=skip, limit=limit)
