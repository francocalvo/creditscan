"""Rules routes module."""

from fastapi import APIRouter

from .create_rule import router as create_rule_router
from .delete_rule import router as delete_rule_router
from .get_rule import router as get_rule_router
from .list_rules import router as list_rules_router
from .update_rule import router as update_rule_router

router = APIRouter(prefix="/rules", tags=["rules"])

router.include_router(create_rule_router)
router.include_router(list_rules_router)
router.include_router(get_rule_router)
router.include_router(update_rule_router)
router.include_router(delete_rule_router)

__all__ = ["router"]
