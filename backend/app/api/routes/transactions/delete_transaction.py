"""Delete transaction endpoint."""

import uuid

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser
from app.domains.card_statements.domain.errors import CardStatementNotFoundError
from app.domains.card_statements.usecases import provide_get_statement
from app.domains.transactions.domain.errors import TransactionNotFoundError
from app.domains.transactions.usecases.delete_transaction import (
    provide as provide_delete_transaction,
)
from app.domains.transactions.usecases.get_transaction import (
    provide as provide_get_transaction,
)

router = APIRouter()


@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(
    transaction_id: uuid.UUID,
    current_user: CurrentUser,
) -> None:
    """Delete a transaction.

    Users can only delete transactions for statements they own.
    Superusers can delete any transaction.
    """
    try:
        # First, check if the transaction exists and verify ownership
        get_transaction_usecase = provide_get_transaction()
        existing_transaction = get_transaction_usecase.execute(transaction_id)

        # Verify ownership through the statement
        get_statement_usecase = provide_get_statement()
        statement = get_statement_usecase.execute(existing_transaction.statement_id)

        if statement.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to delete this transaction",
            )

        # Delete the transaction
        delete_usecase = provide_delete_transaction()
        delete_usecase.execute(transaction_id)
    except TransactionNotFoundError:
        raise HTTPException(status_code=404, detail="Transaction not found")
    except CardStatementNotFoundError:
        raise HTTPException(status_code=404, detail="Card statement not found")
