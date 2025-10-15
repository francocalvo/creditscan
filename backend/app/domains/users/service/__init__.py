"""User service."""

from .user_service import UserService, provide
from .user_service import provide as provide_user_service

__all__ = ["UserService", "provide"]
