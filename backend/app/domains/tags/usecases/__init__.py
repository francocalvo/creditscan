"""Tag usecases."""

from .create_tag import CreateTagUseCase
from .create_tag import provide as provide_create_tag
from .delete_tag import DeleteTagUseCase
from .delete_tag import provide as provide_delete_tag
from .get_tag import GetTagUseCase
from .get_tag import provide as provide_get_tag
from .list_tags import ListTagsUseCase
from .list_tags import provide as provide_list_tags
from .update_tag import UpdateTagUseCase
from .update_tag import provide as provide_update_tag

__all__ = [
    "CreateTagUseCase",
    "DeleteTagUseCase",
    "GetTagUseCase",
    "ListTagsUseCase",
    "UpdateTagUseCase",
    "provide_create_tag",
    "provide_delete_tag",
    "provide_get_tag",
    "provide_list_tags",
    "provide_update_tag",
]
