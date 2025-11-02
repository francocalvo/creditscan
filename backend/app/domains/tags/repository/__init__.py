"""Tag repository."""

from .tag_repository import TagRepository
from .tag_repository import provide as provide_tag_repository

__all__ = [
    "TagRepository",
    "provide_tag_repository",
]
