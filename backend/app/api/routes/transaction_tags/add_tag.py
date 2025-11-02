"""Add tag to transaction endpoint."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser
from app.domains.card_statements.domain.errors import CardStatementNotFoundError
from app.domains.card_statements.usecases import provide_get_statement
from app.domains.tags.domain.errors import TagNotFoundError
from app.domains.tags.usecases import provide_get_tag
from app.domains.transaction_tags.domain.errors import (
    InvalidTransactionTagDataError,
)
from app.domains.transaction_tags.domain.models import (
    TransactionTagCreate,
    TransactionTagPublic,
)
from app.domains.transaction_tags.usecases import provide_add_tag
from app.domains.transactions.domain.errors import TransactionNotFoundError
from app.domains.transactions.usecases import provide_get_transaction

router = APIRouter()


@router.post("/", response_model=TransactionTagPublic, status_code=201)
def add_tag_to_transaction(
    transaction_tag_in: TransactionTagCreate,
    current_user: CurrentUser,
) -> Any:
    """Add a tag to a transaction.

    Users can only add tags to transactions they own.
    Superusers can add tags to any transaction.
    """
    try:
        # Verify that the transaction exists and belongs to the user
        get_transaction_usecase = provide_get_transaction()
        transaction = get_transaction_usecase.execute(transaction_tag_in.transaction_id)

        # Verify ownership through the statement
        get_statement_usecase = provide_get_statement()
        statement = get_statement_usecase.execute(transaction.statement_id)

        if statement.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to add tags to this transaction",
            )

        # Verify that the tag exists and belongs to the user
        get_tag_usecase = provide_get_tag()
        tag = get_tag_usecase.execute(transaction_tag_in.tag_id)

        if tag.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to use this tag",
            )

        # Add the tag to the transaction
        usecase = provide_add_tag()
        return usecase.execute(transaction_tag_in)
    except TransactionNotFoundError:
        raise HTTPException(status_code=404, detail="Transaction not found")
    except TagNotFoundError:
        raise HTTPException(status_code=404, detail="Tag not found")
    except CardStatementNotFoundError:
        raise HTTPException(status_code=404, detail="Card statement not found")
    except InvalidTransactionTagDataError as e:
        raise HTTPException(status_code=400, detail=str(e))
