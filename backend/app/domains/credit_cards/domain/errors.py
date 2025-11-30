"""Credit card domain errors."""


class CreditCardError(Exception):
    """Base exception for credit card errors."""

    pass


class CreditCardNotFoundError(CreditCardError):
    """Raised when a credit card is not found."""

    pass


class InvalidCreditCardDataError(CreditCardError):
    """Raised when credit card data is invalid."""

    pass
