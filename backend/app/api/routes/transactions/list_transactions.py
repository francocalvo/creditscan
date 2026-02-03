"""List transactions endpoint."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.domains.card_statements.domain.errors import CardStatementNotFoundError
from app.domains.card_statements.usecases.get_statement import (
    provide as provide_get_statement,
)
from app.domains.credit_cards.domain.errors import CreditCardNotFoundError
from app.domains.credit_cards.usecases.get_card import provide as provide_get_card
from app.domains.transactions.domain.models import TransactionsPublic
from app.domains.transactions.usecases.list_transactions import (
    provide as provide_list_transactions,
)

router = APIRouter()


@router.get("/", response_model=TransactionsPublic)
def list_transactions(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    statement_id: uuid.UUID | None = None,
) -> Any:
    """Retrieve transactions.

    If statement_id is provided, returns transactions for that statement.
    Users can only view transactions for statements they own (via credit card ownership).
    Superusers can view transactions for any statement.
    """
    if statement_id:
        # Verify that the statement exists and belongs to the user via credit card
        try:
            get_statement_usecase = provide_get_statement(session)
            statement = get_statement_usecase.execute(statement_id)

            # Check ownership through the credit card
            get_card_usecase = provide_get_card(session)
            card = get_card_usecase.execute(statement.card_id)

            if card.user_id != current_user.id and not current_user.is_superuser:
                raise HTTPException(
                    status_code=403,
                    detail="You don't have permission to view transactions for this statement",
                )
        except CardStatementNotFoundError:
            raise HTTPException(status_code=404, detail="Card statement not found")
        except CreditCardNotFoundError:
            raise HTTPException(status_code=404, detail="Credit card not found")

    usecase = provide_list_transactions(session)
    return usecase.execute(skip=skip, limit=limit, statement_id=statement_id)
