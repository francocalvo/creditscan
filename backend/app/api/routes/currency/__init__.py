"""Currency routes module."""

from fastapi import APIRouter

from .convert import router as convert_router
from .extract import router as extract_router
from .rates import router as rates_router

router = APIRouter(prefix="/currency", tags=["currency"])
router.include_router(convert_router)
router.include_router(extract_router)
router.include_router(rates_router)

__all__ = ["router"]
