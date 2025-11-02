"""List transactions endpoint."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser
from app.domains.card_statements.domain.errors import CardStatementNotFoundError
from app.domains.card_statements.usecases import provide_get_statement
from app.domains.transactions.domain.models import TransactionsPublic
from app.domains.transactions.usecases.list_transactions import (
    provide as provide_list_transactions,
)

router = APIRouter()


@router.get("/", response_model=TransactionsPublic)
def list_transactions(
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    statement_id: uuid.UUID | None = None,
) -> Any:
    """Retrieve transactions.

    If statement_id is provided, returns transactions for that statement.
    Users can only view transactions for statements they own.
    Superusers can view transactions for any statement.
    """
    if statement_id:
        # Verify that the statement exists and belongs to the user
        try:
            get_statement_usecase = provide_get_statement()
            statement = get_statement_usecase.execute(statement_id)

            if statement.user_id != current_user.id and not current_user.is_superuser:
                raise HTTPException(
                    status_code=403,
                    detail="You don't have permission to view transactions for this statement",
                )
        except CardStatementNotFoundError:
            raise HTTPException(status_code=404, detail="Card statement not found")

    usecase = provide_list_transactions()
    return usecase.execute(skip=skip, limit=limit, statement_id=statement_id)
