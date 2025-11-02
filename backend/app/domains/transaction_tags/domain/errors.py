"""Transaction tag domain errors."""


class TransactionTagError(Exception):
    """Base exception for transaction tag errors."""

    pass


class TransactionTagNotFoundError(TransactionTagError):
    """Raised when a transaction tag relationship is not found."""

    pass


class InvalidTransactionTagDataError(TransactionTagError):
    """Raised when transaction tag data is invalid."""

    pass
