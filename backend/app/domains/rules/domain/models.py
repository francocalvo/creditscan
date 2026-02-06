"""Rules domain models."""

import uuid
from datetime import datetime
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel


class ConditionField(str, Enum):
    """Fields that can be matched in rule conditions."""

    PAYEE = "payee"
    DESCRIPTION = "description"
    AMOUNT = "amount"
    DATE = "date"


class ConditionOperator(str, Enum):
    """Operators for condition matching."""

    # String operators
    CONTAINS = "contains"
    EQUALS = "equals"
    # Numeric operators
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    # Date operators
    BEFORE = "before"
    AFTER = "after"
    BETWEEN = "between"


class LogicalOperator(str, Enum):
    """Logical operators for combining conditions."""

    AND = "AND"
    OR = "OR"


class ActionType(str, Enum):
    """Types of actions a rule can perform."""

    ADD_TAG = "add_tag"


# Base models
class RuleBase(SQLModel):
    """Base model for Rule with shared fields."""

    name: str = Field(max_length=200)
    is_active: bool = Field(default=True)


# Table models
class Rule(RuleBase, table=True):
    """Rule table model."""

    __tablename__ = "rules"

    rule_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = Field(default=None)

    conditions: list["RuleCondition"] = Relationship(
        back_populates="rule", cascade_delete=True
    )
    actions: list["RuleAction"] = Relationship(
        back_populates="rule", cascade_delete=True
    )


class RuleCondition(SQLModel, table=True):
    """RuleCondition table model."""

    __tablename__ = "rule_conditions"

    condition_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    rule_id: uuid.UUID = Field(foreign_key="rules.rule_id", index=True)
    field: ConditionField
    operator: ConditionOperator
    value: str = Field(max_length=500)
    value_secondary: str | None = Field(default=None, max_length=500)
    logical_operator: LogicalOperator = Field(default=LogicalOperator.AND)
    position: int = Field(default=0)

    rule: Rule = Relationship(back_populates="conditions")


class RuleAction(SQLModel, table=True):
    """RuleAction table model."""

    __tablename__ = "rule_actions"

    action_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    rule_id: uuid.UUID = Field(foreign_key="rules.rule_id", index=True)
    action_type: ActionType
    tag_id: uuid.UUID = Field(foreign_key="tags.tag_id")

    rule: Rule = Relationship(back_populates="actions")


# --- API Create Models ---


class RuleConditionCreate(SQLModel):
    """Input schema for creating a condition within a rule."""

    field: ConditionField
    operator: ConditionOperator
    value: str
    value_secondary: str | None = None
    logical_operator: LogicalOperator = LogicalOperator.AND


class RuleActionCreate(SQLModel):
    """Input schema for creating an action within a rule."""

    action_type: ActionType
    tag_id: uuid.UUID


class RuleCreate(RuleBase):
    """Input schema for creating a complete rule with conditions and actions."""

    conditions: list[RuleConditionCreate]
    actions: list[RuleActionCreate]


# --- API Public/Response Models ---


class RuleConditionPublic(SQLModel):
    """Output schema for condition in API responses."""

    condition_id: uuid.UUID
    field: ConditionField
    operator: ConditionOperator
    value: str
    value_secondary: str | None
    logical_operator: LogicalOperator
    position: int


class RuleActionPublic(SQLModel):
    """Output schema for action in API responses."""

    action_id: uuid.UUID
    action_type: ActionType
    tag_id: uuid.UUID


class RulePublic(RuleBase):
    """Output schema for complete rule in API responses."""

    rule_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime | None
    conditions: list[RuleConditionPublic]
    actions: list[RuleActionPublic]


class RulesPublic(SQLModel):
    """Paginated list response for rules."""

    data: list[RulePublic]
    count: int


# --- API Update Model ---


class RuleUpdate(SQLModel):
    """Input schema for partial rule updates."""

    name: str | None = None
    is_active: bool | None = None
    conditions: list[RuleConditionCreate] | None = None
    actions: list[RuleActionCreate] | None = None


# --- Apply Rules Models ---


class RuleMatch(SQLModel):
    """Info about a single rule that matched a transaction."""

    rule_id: uuid.UUID
    rule_name: str
    tags_applied: list[uuid.UUID]


class TransactionMatch(SQLModel):
    """Info about a transaction and which rules matched it."""

    transaction_id: uuid.UUID
    matched_rules: list[RuleMatch]


class ApplyRulesRequest(SQLModel):
    """Input for the apply rules endpoint."""

    statement_id: uuid.UUID | None = None
    transaction_ids: list[uuid.UUID] | None = None


class ApplyRulesResponse(SQLModel):
    """Output for the apply rules endpoint."""

    transactions_processed: int
    tags_applied: int
    details: list[TransactionMatch]
