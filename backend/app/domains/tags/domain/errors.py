"""Tag domain errors."""


class TagError(Exception):
    """Base exception for tag errors."""

    pass


class TagNotFoundError(TagError):
    """Raised when a tag is not found."""

    pass


class InvalidTagDataError(TagError):
    """Raised when tag data is invalid."""

    pass
