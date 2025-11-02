"""
Central model registry.

All SQLModel table models must be imported here to ensure they're registered
with SQLModel.metadata. This ensures:
- Tables are created when init_db() is called
- Alembic can discover models for migrations
- All models are available in one place
"""

from sqlmodel import SQLModel

# Card statement models (table=True: CardStatement)
from app.domains.card_statements.domain.models import (  # noqa
    CardStatement,
    CardStatementBase,
    CardStatementCreate,
    CardStatementPublic,
    CardStatementsPublic,
    CardStatementUpdate,
)

# Tag models (table=True: Tag)
from app.domains.tags.domain.models import (  # noqa
    Tag,
    TagBase,
    TagCreate,
    TagPublic,
    TagsPublic,
    TagUpdate,
)

# Transaction tag models (table=True: TransactionTag)
from app.domains.transaction_tags.domain.models import (  # noqa
    TransactionTag,
    TransactionTagCreate,
    TransactionTagPublic,
)

# Transaction models (table=True: Transaction)
from app.domains.transactions.domain.models import (  # noqa
    Transaction,
    TransactionBase,
    TransactionCreate,
    TransactionPublic,
    TransactionsPublic,
    TransactionUpdate,
)

# Import all domain table models here to register them with SQLModel metadata
# User models (table=True: User)
from app.domains.users.domain.models import (  # noqa
    NewPassword,
    UpdatePassword,
    User,
    UserBase,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)

# Keep the imports available at this module level for backward compatibility
__all__ = [
    "NewPassword",
    "UpdatePassword",
    "User",
    "UserBase",
    "UserCreate",
    "UserPublic",
    "UserRegister",
    "UsersPublic",
    "UserUpdate",
    "UserUpdateMe",
    "CardStatement",
    "CardStatementBase",
    "CardStatementCreate",
    "CardStatementPublic",
    "CardStatementsPublic",
    "CardStatementUpdate",
    "Transaction",
    "TransactionBase",
    "TransactionCreate",
    "TransactionPublic",
    "TransactionsPublic",
    "TransactionUpdate",
    "Tag",
    "TagBase",
    "TagCreate",
    "TagPublic",
    "TagsPublic",
    "TagUpdate",
    "TransactionTag",
    "TransactionTagCreate",
    "TransactionTagPublic",
]


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None
