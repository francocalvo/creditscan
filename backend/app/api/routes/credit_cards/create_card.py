"""Create credit card endpoint."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.domains.credit_cards.domain.errors import InvalidCreditCardDataError
from app.domains.credit_cards.domain.models import (
    CreditCardCreate,
    CreditCardPublic,
)
from app.domains.credit_cards.usecases.create_card import provide

router = APIRouter()


@router.post("/", response_model=CreditCardPublic, status_code=201)
def create_credit_card(
    session: SessionDep,
    card_in: CreditCardCreate,
    current_user: CurrentUser,
) -> Any:
    """Create a new credit card.

    Users can only create cards for themselves.
    Superusers can create cards for any user.
    """
    # Ensure users can only create cards for themselves
    if not current_user.is_superuser and card_in.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only create cards for yourself",
        )

    try:
        usecase = provide(session)
        return usecase.execute(card_in)
    except InvalidCreditCardDataError as e:
        raise HTTPException(status_code=400, detail=str(e))
