"""Tag service."""

from .tag_service import TagService
from .tag_service import provide as provide_tag_service

__all__ = [
    "TagService",
    "provide_tag_service",
]
