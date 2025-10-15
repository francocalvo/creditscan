"""Get card statement by ID endpoint."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser
from app.domains.card_statements.domain.errors import CardStatementNotFoundError
from app.domains.card_statements.domain.models import CardStatementPublic
from app.domains.card_statements.usecases import provide_get_statement

router = APIRouter()


@router.get("/{statement_id}", response_model=CardStatementPublic)
def get_card_statement(statement_id: uuid.UUID, current_user: CurrentUser) -> Any:
    """Get a specific card statement by ID.

    Users can only view their own statements.
    Superusers can view any statement.
    """
    try:
        usecase = provide_get_statement()
        statement = usecase.execute(statement_id)

        # Allow users to see their own statements, or superusers to see any statement
        if statement.user_id == current_user.id or current_user.is_superuser:
            return statement

        raise HTTPException(
            status_code=403,
            detail="You don't have permission to view this statement",
        )
    except CardStatementNotFoundError:
        raise HTTPException(status_code=404, detail="Card statement not found")
