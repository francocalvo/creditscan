"""Tags routes module."""

from fastapi import APIRouter

from .create_tag import router as create_tag_router
from .delete_tag import router as delete_tag_router
from .get_tag import router as get_tag_router
from .list_tags import router as list_tags_router
from .update_tag import router as update_tag_router

router = APIRouter(prefix="/tags", tags=["tags"])

router.include_router(list_tags_router)
router.include_router(create_tag_router)
router.include_router(get_tag_router)
router.include_router(update_tag_router)
router.include_router(delete_tag_router)

__all__ = ["router"]
