"""Get credit card endpoint."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.domains.credit_cards.domain.errors import CreditCardNotFoundError
from app.domains.credit_cards.domain.models import CreditCardPublic
from app.domains.credit_cards.usecases.get_card import provide

router = APIRouter()


@router.get("/{card_id}", response_model=CreditCardPublic)
def get_credit_card(
    session: SessionDep,
    card_id: uuid.UUID,
    current_user: CurrentUser,
) -> Any:
    """Get a credit card by ID.

    Users can only get their own cards.
    Superusers can get any card.
    """
    try:
        usecase = provide(session)
        card = usecase.execute(card_id)

        # Ensure users can only access their own cards
        if not current_user.is_superuser and card.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can only access your own cards",
            )

        return card
    except CreditCardNotFoundError:
        raise HTTPException(status_code=404, detail="Credit card not found")
