"""Card statement domain errors."""


class CardStatementError(Exception):
    """Base exception for card statement errors."""

    pass


class CardStatementNotFoundError(CardStatementError):
    """Raised when a card statement is not found."""

    pass


class InvalidCardStatementDataError(CardStatementError):
    """Raised when card statement data is invalid."""

    pass
