"""Create card statement endpoint."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser
from app.domains.card_statements.domain.errors import InvalidCardStatementDataError
from app.domains.card_statements.domain.models import (
    CardStatementCreate,
    CardStatementPublic,
)
from app.domains.card_statements.usecases.create_statement import (
    provide as provide_create_statement,
)
from app.domains.credit_cards.usecases.get_card import provide as provide_get_card

router = APIRouter()


@router.post("/", response_model=CardStatementPublic, status_code=201)
def create_card_statement(
    statement_in: CardStatementCreate,
    current_user: CurrentUser,
) -> Any:
    """Create a new card statement.

    Users can only create statements for cards they own.
    Superusers can create statements for any card.
    """
    # Verify the credit card exists and belongs to the user
    try:
        get_card_usecase = provide_get_card()
        card = get_card_usecase.execute(statement_in.card_id)

        # Ensure users can only create statements for their own cards
        if not current_user.is_superuser and card.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can only create statements for your own cards",
            )
    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Credit card not found",
        )

    try:
        usecase = provide_create_statement()
        return usecase.execute(statement_in)
    except InvalidCardStatementDataError as e:
        raise HTTPException(status_code=400, detail=str(e))
