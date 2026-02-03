"""Delete rule endpoint."""

import uuid

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.domains.rules.domain.errors import RuleNotFoundError
from app.domains.rules.usecases.delete_rule import provide as provide_delete_rule

router = APIRouter()


@router.delete("/{rule_id}", status_code=204)
def delete_rule(
    session: SessionDep,
    rule_id: uuid.UUID,
    current_user: CurrentUser,
) -> None:
    """Delete a rule.

    Cascades to delete all conditions and actions.
    Users can only delete their own rules.
    Superusers can delete any rule.
    """
    try:
        usecase = provide_delete_rule(session)
        usecase.execute(rule_id, current_user.id)
    except RuleNotFoundError:
        raise HTTPException(status_code=404, detail="Rule not found")
