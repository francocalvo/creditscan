"""Transaction tag repository."""

from .transaction_tag_repository import TransactionTagRepository
from .transaction_tag_repository import (
    provide as provide_transaction_tag_repository,
)

__all__ = [
    "TransactionTagRepository",
    "provide_transaction_tag_repository",
]
