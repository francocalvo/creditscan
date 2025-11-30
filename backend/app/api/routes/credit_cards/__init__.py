"""Credit cards routes module."""

from fastapi import APIRouter

from .create_card import router as create_card_router
from .delete_card import router as delete_card_router
from .get_card import router as get_card_router
from .list_cards import router as list_cards_router
from .update_card import router as update_card_router

router = APIRouter(prefix="/credit-cards", tags=["credit-cards"])

router.include_router(list_cards_router)
router.include_router(create_card_router)
router.include_router(get_card_router)
router.include_router(update_card_router)
router.include_router(delete_card_router)

__all__ = ["router"]
