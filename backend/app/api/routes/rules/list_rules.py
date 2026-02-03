"""List rules endpoint."""

from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.domains.rules.domain.models import RulesPublic
from app.domains.rules.usecases.list_rules import provide as provide_list_rules

router = APIRouter()


@router.get("/", response_model=RulesPublic)
def list_rules(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """Retrieve rules for the current user.

    Returns paginated list of rules belonging to the authenticated user.
    """
    usecase = provide_list_rules(session)
    return usecase.execute(user_id=current_user.id, skip=skip, limit=limit)
