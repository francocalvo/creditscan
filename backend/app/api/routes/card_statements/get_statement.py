"""Get card statement by ID endpoint."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.domains.card_statements.domain.errors import CardStatementNotFoundError
from app.domains.card_statements.domain.models import CardStatementPublic
from app.domains.card_statements.usecases.get_statement import (
    provide as provide_get_statement,
)
from app.domains.credit_cards.domain.errors import CreditCardNotFoundError
from app.domains.credit_cards.usecases.get_card import provide as provide_get_card

router = APIRouter()


@router.get("/{statement_id}", response_model=CardStatementPublic)
def get_card_statement(
    session: SessionDep, statement_id: uuid.UUID, current_user: CurrentUser
) -> Any:
    """Get a specific card statement by ID.

    Users can only view their own statements.
    Superusers can view any statement.
    """
    try:
        usecase = provide_get_statement(session)
        statement = usecase.execute(statement_id)

        # Allow users to see statements for credit cards they own, or superusers to see any
        get_card_usecase = provide_get_card(session)
        card = get_card_usecase.execute(statement.card_id)

        if card.user_id == current_user.id or current_user.is_superuser:
            return statement

        raise HTTPException(
            status_code=403,
            detail="You don't have permission to view this statement",
        )
    except CardStatementNotFoundError:
        raise HTTPException(status_code=404, detail="Card statement not found")
    except CreditCardNotFoundError:
        raise HTTPException(status_code=404, detail="Credit card not found")
