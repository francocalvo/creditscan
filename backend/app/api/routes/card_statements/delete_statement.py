"""Delete card statement endpoint."""

import uuid

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.domains.card_statements.domain.errors import CardStatementNotFoundError
from app.domains.card_statements.usecases.delete_statement import (
    provide as provide_delete_statement,
)
from app.domains.card_statements.usecases.get_statement import (
    provide as provide_get_statement,
)
from app.domains.credit_cards.domain.errors import CreditCardNotFoundError
from app.domains.credit_cards.usecases.get_card import provide as provide_get_card

router = APIRouter()


@router.delete("/{statement_id}", status_code=204)
def delete_card_statement(
    session: SessionDep,
    statement_id: uuid.UUID,
    current_user: CurrentUser,
) -> None:
    """Delete a card statement.

    Users can only delete their own statements.
    Superusers can delete any statement.
    """
    try:
        # First, check if the statement exists and belongs to the user
        get_usecase = provide_get_statement(session)
        existing_statement = get_usecase.execute(statement_id)

        get_card_usecase = provide_get_card(session)
        card = get_card_usecase.execute(existing_statement.card_id)

        if card.user_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to delete this statement",
            )

        # Delete the statement
        delete_usecase = provide_delete_statement(session)
        delete_usecase.execute(statement_id)
    except CardStatementNotFoundError:
        raise HTTPException(status_code=404, detail="Card statement not found")
    except CreditCardNotFoundError:
        raise HTTPException(status_code=404, detail="Credit card not found")
