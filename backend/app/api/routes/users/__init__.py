"""Users routes module."""

from fastapi import APIRouter

from .create_user import router as create_user_router
from .delete_me import router as delete_me_router
from .delete_user import router as delete_user_router
from .get_balance import router as get_balance_router
from .get_me import router as get_me_router
from .get_user import router as get_user_router
from .signup import router as signup_router
from .update_me import router as update_me_router
from .update_password_me import router as update_password_me_router
from .update_user import router as update_user_router

router = APIRouter(prefix="/users", tags=["users"])

# Include all user routes
router.include_router(create_user_router)
router.include_router(get_me_router)
router.include_router(get_balance_router)
router.include_router(update_me_router)
router.include_router(update_password_me_router)
router.include_router(delete_me_router)
router.include_router(signup_router)
router.include_router(get_user_router)
router.include_router(update_user_router)
router.include_router(delete_user_router)

__all__ = ["router"]
