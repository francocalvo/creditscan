"""Transaction tags routes module."""

from fastapi import APIRouter

from .add_tag import router as add_tag_router
from .get_tags import router as get_tags_router
from .get_tags_batch import router as get_tags_batch_router
from .remove_tag import router as remove_tag_router

router = APIRouter(prefix="/transaction-tags", tags=["transaction-tags"])

router.include_router(add_tag_router)
router.include_router(get_tags_router)
router.include_router(get_tags_batch_router)
router.include_router(remove_tag_router)

__all__ = ["router"]
