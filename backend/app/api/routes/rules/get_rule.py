"""Get rule by ID endpoint."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.domains.rules.domain.errors import RuleNotFoundError
from app.domains.rules.domain.models import RulePublic
from app.domains.rules.usecases.get_rule import provide as provide_get_rule

router = APIRouter()


@router.get("/{rule_id}", response_model=RulePublic)
def get_rule(
    session: SessionDep,
    rule_id: uuid.UUID,
    current_user: CurrentUser,
) -> Any:
    """Get a specific rule by ID.

    Users can only view their own rules.
    Superusers can view any rule.
    """
    try:
        usecase = provide_get_rule(session)
        return usecase.execute(rule_id, current_user.id)
    except RuleNotFoundError:
        raise HTTPException(status_code=404, detail="Rule not found")
