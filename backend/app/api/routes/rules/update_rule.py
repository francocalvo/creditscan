"""Update rule endpoint."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.domains.rules.domain.errors import (
    RuleNotFoundError,
    RuleValidationError,
    TagNotFoundForActionError,
)
from app.domains.rules.domain.models import RulePublic, RuleUpdate
from app.domains.rules.usecases.update_rule import provide as provide_update_rule

router = APIRouter()


@router.put("/{rule_id}", response_model=RulePublic)
def update_rule(
    session: SessionDep,
    rule_id: uuid.UUID,
    rule_in: RuleUpdate,
    current_user: CurrentUser,
) -> Any:
    """Update a rule.

    Replaces the rule's conditions and actions with the provided data.
    Users can only update their own rules.
    Superusers can update any rule.
    """
    try:
        usecase = provide_update_rule(session)
        return usecase.execute(rule_id, current_user.id, rule_in)
    except RuleNotFoundError:
        raise HTTPException(status_code=404, detail="Rule not found")
    except RuleValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TagNotFoundForActionError as e:
        raise HTTPException(status_code=400, detail=str(e))
