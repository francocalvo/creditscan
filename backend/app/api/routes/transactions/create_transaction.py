"""Create transaction endpoint."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.domains.card_statements.domain.errors import CardStatementNotFoundError
from app.domains.card_statements.usecases.get_statement import (
    provide as provide_get_statement,
)
from app.domains.transactions.domain.errors import InvalidTransactionDataError
from app.domains.transactions.domain.models import (
    TransactionCreate,
    TransactionPublic,
)
from app.domains.transactions.usecases.create_transaction import (
    provide as provide_create_transaction,
)

router = APIRouter()


@router.post("/", response_model=TransactionPublic, status_code=201)
def create_transaction(
    session: SessionDep,
    transaction_in: TransactionCreate,
    current_user: CurrentUser,
) -> Any:
    """Create a new transaction.

    Users can only create transactions for statements they own.
    Superusers can create transactions for any statement.
    """
    try:
        # Verify that the statement exists and belongs to the user
        get_statement_usecase = provide_get_statement(session)
        statement = get_statement_usecase.execute(transaction_in.statement_id)

        if statement.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to create transactions for this statement",
            )

        # Create the transaction
        usecase = provide_create_transaction(session)
        return usecase.execute(transaction_in)
    except CardStatementNotFoundError:
        raise HTTPException(status_code=404, detail="Card statement not found")
    except InvalidTransactionDataError as e:
        raise HTTPException(status_code=400, detail=str(e))
