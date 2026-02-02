"""Update credit card endpoint."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.domains.credit_cards.domain.errors import CreditCardNotFoundError
from app.domains.credit_cards.domain.models import (
    CreditCardPublic,
    CreditCardUpdate,
)
from app.domains.credit_cards.usecases.get_card import provide as provide_get_card
from app.domains.credit_cards.usecases.update_card import provide as provide_update_card

router = APIRouter()


@router.patch("/{card_id}", response_model=CreditCardPublic)
def update_credit_card(
    session: SessionDep,
    card_id: uuid.UUID,
    card_in: CreditCardUpdate,
    current_user: CurrentUser,
) -> Any:
    """Update a credit card.

    Users can only update their own cards.
    Superusers can update any card.
    """
    try:
        # First check if the card exists and belongs to the user
        get_usecase = provide_get_card(session)
        card = get_usecase.execute(card_id)

        # Ensure users can only update their own cards
        if not current_user.is_superuser and card.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can only update your own cards",
            )

        update_usecase = provide_update_card(session)
        return update_usecase.execute(card_id, card_in)
    except CreditCardNotFoundError:
        raise HTTPException(status_code=404, detail="Credit card not found")
