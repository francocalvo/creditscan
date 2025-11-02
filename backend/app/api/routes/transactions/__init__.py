"""Transactions routes module."""

from fastapi import APIRouter

from .create_transaction import router as create_transaction_router
from .delete_transaction import router as delete_transaction_router
from .get_transaction import router as get_transaction_router
from .list_transactions import router as list_transactions_router
from .update_transaction import router as update_transaction_router

router = APIRouter(prefix="/transactions", tags=["transactions"])

router.include_router(list_transactions_router)
router.include_router(create_transaction_router)
router.include_router(get_transaction_router)
router.include_router(update_transaction_router)
router.include_router(delete_transaction_router)

__all__ = ["router"]
