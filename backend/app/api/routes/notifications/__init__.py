"""Notifications routes module."""

from fastapi import APIRouter

from .trigger import router as trigger_router

router = APIRouter(prefix="/notifications", tags=["notifications"])

router.include_router(trigger_router)

__all__ = ["router"]
