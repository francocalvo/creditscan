"""Create rule endpoint."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.domains.rules.domain.errors import (
    RuleValidationError,
    TagNotFoundForActionError,
)
from app.domains.rules.domain.models import RuleCreate, RulePublic
from app.domains.rules.usecases.create_rule import provide as provide_create_rule

router = APIRouter()


@router.post("/", response_model=RulePublic, status_code=201)
def create_rule(
    session: SessionDep,
    rule_in: RuleCreate,
    current_user: CurrentUser,
) -> Any:
    """Create a new rule.

    Users can only create rules for themselves.
    Superusers can create rules for any user.
    """
    try:
        usecase = provide_create_rule(session)
        return usecase.execute(rule_in, current_user.id)
    except RuleValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TagNotFoundForActionError as e:
        raise HTTPException(status_code=400, detail=str(e))
