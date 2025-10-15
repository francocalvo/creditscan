"""Get current user endpoint."""

from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.domains.users.domain.models import UserPublic

router = APIRouter()


@router.get("/me", response_model=UserPublic)
def get_current_user(current_user: CurrentUser) -> Any:
    """Get current user."""
    return current_user
