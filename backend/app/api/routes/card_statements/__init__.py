"""Card statements routes module."""

from fastapi import APIRouter

from .create_statement import router as create_statement_router
from .delete_statement import router as delete_statement_router
from .get_statement import router as get_statement_router
from .list_statements import router as list_statements_router
from .update_statement import router as update_statement_router
from .upload_statement import router as upload_statement_router

router = APIRouter(prefix="/card-statements", tags=["card-statements"])

router.include_router(list_statements_router)
router.include_router(create_statement_router)
router.include_router(get_statement_router)
router.include_router(update_statement_router)
router.include_router(delete_statement_router)
router.include_router(upload_statement_router)

__all__ = ["router"]
