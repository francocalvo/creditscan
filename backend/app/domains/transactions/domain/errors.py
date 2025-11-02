"""Transaction domain errors."""


class TransactionError(Exception):
    """Base exception for transaction errors."""

    pass


class TransactionNotFoundError(TransactionError):
    """Raised when a transaction is not found."""

    pass


class InvalidTransactionDataError(TransactionError):
    """Raised when transaction data is invalid."""

    pass
