"""Get tags for transaction endpoint."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.domains.card_statements.domain.errors import CardStatementNotFoundError
from app.domains.card_statements.repository import (
    provide as provide_card_statement_repo,
)
from app.domains.credit_cards.repository import provide as provide_credit_card_repo
from app.domains.transaction_tags.domain.models import TransactionTagPublic
from app.domains.transaction_tags.usecases.get_tags import provide as provide_get_tags
from app.domains.transactions.domain.errors import TransactionNotFoundError
from app.domains.transactions.usecases.get_transaction import (
    provide as provide_get_transaction,
)

router = APIRouter()


@router.get("/transaction/{transaction_id}", response_model=list[TransactionTagPublic])
def get_transaction_tags(
    session: SessionDep, transaction_id: uuid.UUID, current_user: CurrentUser
) -> Any:
    """Get all tags for a transaction.

    Users can only view tags for transactions they own.
    Superusers can view tags for any transaction.
    """
    try:
        # Verify that transaction exists and belongs to user
        get_transaction_usecase = provide_get_transaction(session)
        transaction = get_transaction_usecase.execute(transaction_id)

        # Verify ownership through statement -> card -> user
        card_statement_repo = provide_card_statement_repo(session)
        statement = card_statement_repo.get_by_id(transaction.statement_id)

        credit_card_repo = provide_credit_card_repo(session)
        card = credit_card_repo.get_by_id(statement.card_id)

        if card.user_id == current_user.id or current_user.is_superuser:
            usecase = provide_get_tags(session)
            return usecase.execute(transaction_id)

        raise HTTPException(
            status_code=403,
            detail="You don't have permission to view tags for this transaction",
        )
    except TransactionNotFoundError:
        raise HTTPException(status_code=404, detail="Transaction not found")
    except CardStatementNotFoundError:
        raise HTTPException(status_code=404, detail="Card statement not found")
