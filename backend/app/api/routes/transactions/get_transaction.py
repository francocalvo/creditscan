"""Get transaction by ID endpoint."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.domains.card_statements.domain.errors import CardStatementNotFoundError
from app.domains.card_statements.usecases.get_statement import (
    provide as provide_get_statement,
)
from app.domains.transactions.domain.errors import TransactionNotFoundError
from app.domains.transactions.domain.models import TransactionPublic
from app.domains.transactions.usecases.get_transaction import (
    provide as provide_get_transaction,
)

router = APIRouter()


@router.get("/{transaction_id}", response_model=TransactionPublic)
def get_transaction(
    session: SessionDep, transaction_id: uuid.UUID, current_user: CurrentUser
) -> Any:
    """Get a specific transaction by ID.

    Users can only view transactions for statements they own.
    Superusers can view any transaction.
    """
    try:
        usecase = provide_get_transaction(session)
        transaction = usecase.execute(transaction_id)

        # Verify ownership through the statement
        get_statement_usecase = provide_get_statement(session)
        statement = get_statement_usecase.execute(transaction.statement_id)

        if statement.user_id == current_user.id or current_user.is_superuser:
            return transaction

        raise HTTPException(
            status_code=403,
            detail="You don't have permission to view this transaction",
        )
    except TransactionNotFoundError:
        raise HTTPException(status_code=404, detail="Transaction not found")
    except CardStatementNotFoundError:
        raise HTTPException(status_code=404, detail="Card statement not found")
