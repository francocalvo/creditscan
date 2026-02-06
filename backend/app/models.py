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

# Credit card models (table=True: CreditCard)
from app.domains.credit_cards.domain.models import (  # noqa
    CardBrand,
    CreditCard,
    CreditCardBase,
    CreditCardCreate,
    CreditCardPublic,
    CreditCardsPublic,
    CreditCardUpdate,
)

# Currency domain models (table=True: ExchangeRate)
from app.domains.currency.domain.models import (  # noqa
    BatchCurrencyConversionRequest,
    BatchCurrencyConversionResponse,
    CurrencyConversionRequest,
    CurrencyConversionResponse,
    ExchangeRate,
)

# Payment models (table=True: Payment)
from app.domains.payments.domain.models import (  # noqa
    Payment,
    PaymentBase,
    PaymentCreate,
    PaymentPublic,
    PaymentsPublic,
    PaymentUpdate,
)

# Rules domain models (table=True: Rule)
from app.domains.rules.domain.models import (  # noqa
    ActionType,
    ApplyRulesRequest,
    ApplyRulesResponse,
    ConditionField,
    ConditionOperator,
    LogicalOperator,
    Rule,
    RuleAction,
    RuleActionCreate,
    RuleActionPublic,
    RuleBase,
    RuleCondition,
    RuleConditionCreate,
    RuleConditionPublic,
    RuleCreate,
    RuleMatch,
    RulePublic,
    RulesPublic,
    RuleUpdate,
    TransactionMatch,
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

# Upload job models (table=True: UploadJob)
from app.domains.upload_jobs.domain.models import (  # noqa
    UploadJob,
    UploadJobCreate,
    UploadJobPublic,
    UploadJobStatus,
)

# Import all domain table models here to register them with SQLModel metadata
# User models (table=True: User)
from app.domains.users.domain.models import (  # noqa
    NewPassword,
    UpdatePassword,
    User,
    UserBalancePublic,
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
    "UserBalancePublic",
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
    "CreditCard",
    "CreditCardBase",
    "CreditCardCreate",
    "CreditCardPublic",
    "CreditCardsPublic",
    "CreditCardUpdate",
    "CardBrand",
    "Transaction",
    "TransactionBase",
    "TransactionCreate",
    "TransactionPublic",
    "TransactionsPublic",
    "TransactionUpdate",
    "UploadJob",
    "UploadJobCreate",
    "UploadJobPublic",
    "UploadJobStatus",
    "Tag",
    "TagBase",
    "TagCreate",
    "TagPublic",
    "TagsPublic",
    "TagUpdate",
    "TransactionTag",
    "TransactionTagCreate",
    "TransactionTagPublic",
    "Payment",
    "PaymentBase",
    "PaymentCreate",
    "PaymentPublic",
    "PaymentsPublic",
    "PaymentUpdate",
    "ActionType",
    "ApplyRulesRequest",
    "ApplyRulesResponse",
    "ConditionField",
    "ConditionOperator",
    "LogicalOperator",
    "Rule",
    "RuleAction",
    "RuleActionCreate",
    "RuleActionPublic",
    "RuleBase",
    "RuleCondition",
    "RuleConditionCreate",
    "RuleConditionPublic",
    "RuleCreate",
    "RuleMatch",
    "RulePublic",
    "RulesPublic",
    "RuleUpdate",
    "TransactionMatch",
    "ExchangeRate",
    "CurrencyConversionRequest",
    "CurrencyConversionResponse",
    "BatchCurrencyConversionRequest",
    "BatchCurrencyConversionResponse",
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
