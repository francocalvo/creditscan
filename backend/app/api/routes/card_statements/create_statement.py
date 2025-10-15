"""Create card statement endpoint."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser
from app.domains.card_statements.domain.errors import InvalidCardStatementDataError
from app.domains.card_statements.domain.models import (
    CardStatementCreate,
    CardStatementPublic,
)
from app.domains.card_statements.usecases import provide_create_statement

router = APIRouter()


@router.post("/", response_model=CardStatementPublic, status_code=201)
def create_card_statement(
    statement_in: CardStatementCreate,
    current_user: CurrentUser,
) -> Any:
    """Create a new card statement.

    Users can only create statements for themselves.
    Superusers can create statements for any user.
    """
    # Ensure users can only create statements for themselves
    if not current_user.is_superuser and statement_in.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only create statements for yourself",
        )

    try:
        usecase = provide_create_statement()
        return usecase.execute(statement_in)
    except InvalidCardStatementDataError as e:
        raise HTTPException(status_code=400, detail=str(e))
