"""User domain errors."""


class UserError(Exception):
    """Base exception for user errors."""

    pass


class UserNotFoundError(UserError):
    """Raised when a user is not found."""

    pass


class InvalidUserDataError(UserError):
    """Raised when user data is invalid."""

    pass


class InvalidCredentialsError(UserError):
    """Raised when authentication credentials are invalid."""

    pass


class DuplicateUserError(UserError):
    """Raised when attempting to create a user that already exists."""

    pass
