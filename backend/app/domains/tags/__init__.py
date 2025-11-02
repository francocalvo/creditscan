"""Tags domain module."""

from .domain import (
    InvalidTagDataError,
    Tag,
    TagCreate,
    TagError,
    TagNotFoundError,
    TagPublic,
    TagsPublic,
    TagUpdate,
)
from .repository import TagRepository, provide_tag_repository
from .service import TagService, provide_tag_service

__all__ = [
    "Tag",
    "TagCreate",
    "TagError",
    "TagNotFoundError",
    "TagPublic",
    "TagsPublic",
    "TagUpdate",
    "InvalidTagDataError",
    "TagRepository",
    "TagService",
    "provide_tag_repository",
    "provide_tag_service",
]
