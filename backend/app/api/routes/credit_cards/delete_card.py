"""Delete credit card endpoint."""

import uuid

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser
from app.domains.credit_cards.domain.errors import CreditCardNotFoundError
from app.domains.credit_cards.usecases.delete_card import provide as provide_delete_card
from app.domains.credit_cards.usecases.get_card import provide as provide_get_card

router = APIRouter()


@router.delete("/{card_id}", status_code=204)
def delete_credit_card(
    card_id: uuid.UUID,
    current_user: CurrentUser,
) -> None:
    """Delete a credit card.

    Users can only delete their own cards.
    Superusers can delete any card.
    """
    try:
        # First check if the card exists and belongs to the user
        get_usecase = provide_get_card()
        card = get_usecase.execute(card_id)

        # Ensure users can only delete their own cards
        if not current_user.is_superuser and card.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can only delete your own cards",
            )

        delete_usecase = provide_delete_card()
        delete_usecase.execute(card_id)
    except CreditCardNotFoundError:
        raise HTTPException(status_code=404, detail="Credit card not found")
