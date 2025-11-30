"""Payments routes module."""

from fastapi import APIRouter

from .create_payment import router as create_payment_router
from .delete_payment import router as delete_payment_router
from .get_payment import router as get_payment_router
from .list_payments import router as list_payments_router
from .update_payment import router as update_payment_router

router = APIRouter(prefix="/payments", tags=["payments"])

router.include_router(list_payments_router)
router.include_router(create_payment_router)
router.include_router(get_payment_router)
router.include_router(update_payment_router)
router.include_router(delete_payment_router)

__all__ = ["router"]
