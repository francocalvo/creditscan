"""Rule service for managing rules with validation."""

import uuid

from sqlmodel import Session

from app.domains.rules.domain.errors import (
    RuleNotFoundError,
    RuleValidationError,
    TagNotFoundForActionError,
)
from app.domains.rules.domain.models import (
    ConditionField,
    ConditionOperator,
    Rule,
    RuleConditionCreate,
    RuleCreate,
    RulePublic,
    RulesPublic,
    RuleUpdate,
)
from app.domains.rules.repository import RuleRepository
from app.domains.rules.repository import provide as provide_rule_repo
from app.domains.tags.domain.errors import TagNotFoundError
from app.domains.tags.repository import TagRepository
from app.domains.tags.repository import provide as provide_tag_repo


class RuleService:
    """Service for managing rules with validation."""

    def __init__(
        self, rule_repository: RuleRepository, tag_repository: TagRepository
    ) -> None:
        """Initialize the service with repositories.

        Args:
            rule_repository: The rule repository.
            tag_repository: The tag repository for validating tag references.
        """
        self._rule_repo = rule_repository
        self._tag_repo = tag_repository

    def _validate_rule_data(
        self, rule_data: RuleCreate | RuleUpdate, is_create: bool = True
    ) -> None:
        """Validate rule data before create/update.

        Args:
            rule_data: The rule data to validate.
            is_create: Whether this is a create operation (requires conditions/actions).

        Raises:
            RuleValidationError: If validation fails.
            TagNotFoundForActionError: If a tag referenced in an action doesn't exist.
        """
        # For create, conditions and actions are required
        if is_create:
            if not isinstance(rule_data, RuleCreate):
                raise RuleValidationError("Expected RuleCreate for create operation")
            if not rule_data.conditions:
                raise RuleValidationError("Rule must have at least one condition")
            if not rule_data.actions:
                raise RuleValidationError("Rule must have at least one action")

        # For update, only validate if provided
        if isinstance(rule_data, RuleUpdate):
            if rule_data.conditions is not None and len(rule_data.conditions) == 0:
                raise RuleValidationError("Rule must have at least one condition")
            if rule_data.actions is not None and len(rule_data.actions) == 0:
                raise RuleValidationError("Rule must have at least one action")

        # Validate tag references in actions
        actions = None
        if isinstance(rule_data, RuleCreate):
            actions = rule_data.actions
        elif rule_data.actions is not None:
            actions = rule_data.actions

        if actions:
            for action in actions:
                try:
                    # Check if tag exists and is not soft-deleted
                    self._tag_repo.get_by_id(action.tag_id, include_deleted=False)
                except TagNotFoundError:
                    raise TagNotFoundForActionError(str(action.tag_id))

        # Validate conditions
        conditions = None
        if isinstance(rule_data, RuleCreate):
            conditions = rule_data.conditions
        elif rule_data.conditions is not None:
            conditions = rule_data.conditions

        if conditions:
            for condition in conditions:
                self._validate_operator_for_field(condition)
                self._validate_between_requires_value_secondary(condition)

    def _validate_operator_for_field(self, condition: RuleConditionCreate) -> None:
        """Validate that the operator is valid for the field.

        Args:
            condition: The condition to validate.

        Raises:
            RuleValidationError: If the operator is not valid for the field.
        """
        # Operator-Field compatibility matrix
        valid_operators = {
            ConditionField.PAYEE: [
                ConditionOperator.CONTAINS,
                ConditionOperator.EQUALS,
            ],
            ConditionField.DESCRIPTION: [
                ConditionOperator.CONTAINS,
                ConditionOperator.EQUALS,
            ],
            ConditionField.AMOUNT: [
                ConditionOperator.EQUALS,
                ConditionOperator.GT,
                ConditionOperator.LT,
                ConditionOperator.BETWEEN,
            ],
            ConditionField.DATE: [
                ConditionOperator.EQUALS,
                ConditionOperator.BEFORE,
                ConditionOperator.AFTER,
                ConditionOperator.BETWEEN,
            ],
        }

        if condition.field not in valid_operators:
            # Shouldn't happen with enum, but defensive check
            raise RuleValidationError(
                f"Unknown field: {condition.field}. Valid fields: payee, description, amount, date"
            )

        valid_ops = valid_operators[condition.field]
        if condition.operator not in valid_ops:
            op_list = ", ".join(op.value for op in valid_ops)
            raise RuleValidationError(
                f"Operator '{condition.operator.value}' is not valid for field '{condition.field.value}'. Valid operators: {op_list}"
            )

    def _validate_between_requires_value_secondary(
        self, condition: RuleConditionCreate
    ) -> None:
        """Validate that BETWEEN operator has value_secondary.

        Args:
            condition: The condition to validate.

        Raises:
            RuleValidationError: If value_secondary is missing for BETWEEN.
        """
        if (
            condition.operator == ConditionOperator.BETWEEN
            and condition.value_secondary is None
        ):
            raise RuleValidationError(
                "Operator 'between' requires 'value_secondary' to be set"
            )

    def _check_user_owns_rule(self, rule: Rule, user_id: uuid.UUID) -> None:
        """Check if the user owns the rule.

        Args:
            rule: The rule to check.
            user_id: The user ID to check against.

        Raises:
            RuleNotFoundError: If the user doesn't own the rule (to avoid leaking existence).
        """
        if rule.user_id != user_id:
            raise RuleNotFoundError(str(rule.rule_id))

    def _to_public(self, rule: Rule) -> RulePublic:
        """Convert a Rule model to RulePublic.

        Args:
            rule: The rule to convert.

        Returns:
            The RulePublic representation.
        """
        return RulePublic.model_validate(rule)

    def create_rule(self, rule_data: RuleCreate, user_id: uuid.UUID) -> RulePublic:
        """Create a new rule.

        Args:
            rule_data: The rule data.
            user_id: The ID of the user creating the rule.

        Returns:
            The created rule.

        Raises:
            RuleValidationError: If validation fails.
            TagNotFoundForActionError: If a tag doesn't exist.
        """
        self._validate_rule_data(rule_data, is_create=True)
        rule = self._rule_repo.create(rule_data, user_id)
        return self._to_public(rule)

    def get_rule(self, rule_id: uuid.UUID, user_id: uuid.UUID) -> RulePublic:
        """Get a rule by ID.

        Args:
            rule_id: The ID of the rule to retrieve.
            user_id: The ID of the requesting user.

        Returns:
            The rule.

        Raises:
            RuleNotFoundError: If the rule doesn't exist or user doesn't own it.
        """
        rule = self._rule_repo.get_by_id(rule_id)
        self._check_user_owns_rule(rule, user_id)
        return self._to_public(rule)

    def list_rules(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> RulesPublic:
        """List rules for a user.

        Args:
            user_id: The ID of the user.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            Paginated list of rules.
        """
        filters = {"user_id": user_id}
        rules = self._rule_repo.list(skip=skip, limit=limit, filters=filters)
        count = self._rule_repo.count(filters=filters)
        return RulesPublic(
            data=[self._to_public(rule) for rule in rules],
            count=count,
        )

    def update_rule(
        self, rule_id: uuid.UUID, user_id: uuid.UUID, rule_data: RuleUpdate
    ) -> RulePublic:
        """Update a rule.

        Args:
            rule_id: The ID of the rule to update.
            user_id: The ID of the requesting user.
            rule_data: The update data.

        Returns:
            The updated rule.

        Raises:
            RuleNotFoundError: If the rule doesn't exist or user doesn't own it.
            RuleValidationError: If validation fails.
            TagNotFoundForActionError: If a tag doesn't exist.
        """
        # Check ownership first
        rule = self._rule_repo.get_by_id(rule_id)
        self._check_user_owns_rule(rule, user_id)

        # Validate the update data
        self._validate_rule_data(rule_data, is_create=False)

        # Perform the update
        updated_rule = self._rule_repo.update(rule_id, rule_data)
        return self._to_public(updated_rule)

    def delete_rule(self, rule_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete a rule.

        Args:
            rule_id: The ID of the rule to delete.
            user_id: The ID of the requesting user.

        Raises:
            RuleNotFoundError: If the rule doesn't exist or user doesn't own it.
        """
        rule = self._rule_repo.get_by_id(rule_id)
        self._check_user_owns_rule(rule, user_id)
        self._rule_repo.delete(rule_id)


def provide(session: Session) -> RuleService:
    """Provide an instance of RuleService.

    Args:
        session: The database session to use.

    Returns:
        RuleService: An instance of RuleService with the given session.
    """
    rule_repo = provide_rule_repo(session)
    tag_repo = provide_tag_repo(session)
    return RuleService(rule_repo, tag_repo)
