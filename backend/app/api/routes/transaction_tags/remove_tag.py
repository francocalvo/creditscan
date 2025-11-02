"""Remove tag from transaction endpoint."""

import uuid

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser
from app.domains.card_statements.domain.errors import CardStatementNotFoundError
from app.domains.card_statements.usecases import provide_get_statement
from app.domains.transaction_tags.domain.errors import (
    TransactionTagNotFoundError,
)
from app.domains.transaction_tags.usecases import provide_remove_tag
from app.domains.transactions.domain.errors import TransactionNotFoundError
from app.domains.transactions.usecases import provide_get_transaction

router = APIRouter()


@router.delete("/transaction/{transaction_id}/tag/{tag_id}", status_code=204)
def remove_tag_from_transaction(
    transaction_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: CurrentUser,
) -> None:
    """Remove a tag from a transaction.

    Users can only remove tags from transactions they own.
    Superusers can remove tags from any transaction.
    """
    try:
        # Verify that the transaction exists and belongs to the user
        get_transaction_usecase = provide_get_transaction()
        transaction = get_transaction_usecase.execute(transaction_id)

        # Verify ownership through the statement
        get_statement_usecase = provide_get_statement()
        statement = get_statement_usecase.execute(transaction.statement_id)

        if statement.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to remove tags from this transaction",
            )

        # Remove the tag from the transaction
        usecase = provide_remove_tag()
        usecase.execute(transaction_id, tag_id)
    except TransactionNotFoundError:
        raise HTTPException(status_code=404, detail="Transaction not found")
    except CardStatementNotFoundError:
        raise HTTPException(status_code=404, detail="Card statement not found")
    except TransactionTagNotFoundError:
        raise HTTPException(
            status_code=404, detail="Transaction tag relationship not found"
        )
