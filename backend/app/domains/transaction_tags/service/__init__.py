"""Transaction tag service."""

from .transaction_tag_service import TransactionTagService
from .transaction_tag_service import (
    provide as provide_transaction_tag_service,
)

__all__ = [
    "TransactionTagService",
    "provide_transaction_tag_service",
]
