"""Update card statement endpoint."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.domains.card_statements.domain.errors import (
    CardStatementNotFoundError,
    InvalidCardStatementDataError,
)
from app.domains.card_statements.domain.models import (
    CardStatementPublic,
    CardStatementUpdate,
)
from app.domains.card_statements.usecases.get_statement import (
    provide as provide_get_statement,
)
from app.domains.card_statements.usecases.update_statement import (
    provide as provide_update_statement,
)
from app.domains.credit_cards.domain.errors import CreditCardNotFoundError
from app.domains.credit_cards.usecases.get_card import provide as provide_get_card

router = APIRouter()


@router.patch("/{statement_id}", response_model=CardStatementPublic)
def update_card_statement(
    session: SessionDep,
    statement_id: uuid.UUID,
    statement_in: CardStatementUpdate,
    current_user: CurrentUser,
) -> Any:
    """Update a card statement.

    Users can only update their own statements.
    Superusers can update any statement.
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
                detail="You don't have permission to update this statement",
            )

        # Update the statement
        update_usecase = provide_update_statement(session)
        return update_usecase.execute(statement_id, statement_in)
    except CardStatementNotFoundError:
        raise HTTPException(status_code=404, detail="Card statement not found")
    except CreditCardNotFoundError:
        raise HTTPException(status_code=404, detail="Credit card not found")
    except InvalidCardStatementDataError as e:
        raise HTTPException(status_code=400, detail=str(e))
