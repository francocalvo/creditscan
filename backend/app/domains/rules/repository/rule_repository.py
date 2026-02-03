"""Rule repository implementation."""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlmodel import Session, delete, func, select

from app.domains.rules.domain.errors import RuleNotFoundError
from app.domains.rules.domain.models import (
    Rule,
    RuleAction,
    RuleCondition,
    RuleCreate,
    RuleUpdate,
)


class RuleRepository:
    """Repository for rules."""

    def __init__(self, db_session: Session):
        """Initialize the repository with a database session."""
        self.db_session = db_session

    def create(self, rule_data: RuleCreate, user_id: uuid.UUID) -> Rule:
        """Create a new rule with nested conditions and actions.

        Args:
            rule_data: The rule data including conditions and actions.
            user_id: The ID of the user who owns this rule.

        Returns:
            The created rule with conditions and actions.
        """
        # Create parent rule
        rule = Rule(
            name=rule_data.name,
            is_active=rule_data.is_active,
            user_id=user_id,
        )
        self.db_session.add(rule)
        self.db_session.flush()  # Get rule_id for FK in children

        # Create conditions with position assignment
        for position, condition_data in enumerate(rule_data.conditions):
            condition = RuleCondition(
                rule_id=rule.rule_id,
                field=condition_data.field,
                operator=condition_data.operator,
                value=condition_data.value,
                value_secondary=condition_data.value_secondary,
                logical_operator=condition_data.logical_operator,
                position=position,
            )
            self.db_session.add(condition)

        # Create actions
        for action_data in rule_data.actions:
            action = RuleAction(
                rule_id=rule.rule_id,
                action_type=action_data.action_type,
                tag_id=action_data.tag_id,
            )
            self.db_session.add(action)

        self.db_session.commit()
        self.db_session.refresh(rule)
        return rule

    def get_by_id(self, rule_id: uuid.UUID) -> Rule:
        """Get a rule by ID.

        Args:
            rule_id: The ID of the rule to retrieve.

        Returns:
            The rule with the specified ID.

        Raises:
            RuleNotFoundError: If the rule is not found.
        """
        rule = self.db_session.get(Rule, rule_id)
        if not rule:
            raise RuleNotFoundError(str(rule_id))
        return rule

    def list(
        self, skip: int = 0, limit: int = 100, filters: dict[str, Any] | None = None
    ) -> list[Rule]:
        """List rules with pagination and filtering.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            filters: Optional dict of field names and values to filter by.

        Returns:
            List of rules matching the criteria.
        """
        query = select(Rule)

        if filters:
            for field, value in filters.items():
                if hasattr(Rule, field):
                    query = query.where(getattr(Rule, field) == value)

        result = self.db_session.exec(query.offset(skip).limit(limit))
        return list(result)

    def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count rules with optional filtering.

        Args:
            filters: Optional dict of field names and values to filter by.

        Returns:
            Number of rules matching the criteria.
        """
        query = select(Rule)

        if filters:
            for field, value in filters.items():
                if hasattr(Rule, field):
                    query = query.where(getattr(Rule, field) == value)

        count_q = (
            query.with_only_columns(func.count())
            .order_by(None)
            .select_from(query.get_final_froms()[0])
        )

        result = self.db_session.exec(count_q)
        for count in result:
            return count  # type: ignore
        return 0

    def update(self, rule_id: uuid.UUID, rule_data: RuleUpdate) -> Rule:
        """Update a rule.

        If conditions or actions are provided, they replace all existing
        conditions/actions for this rule.

        Args:
            rule_id: The ID of the rule to update.
            rule_data: The update data.

        Returns:
            The updated rule.
        """
        rule = self.get_by_id(rule_id)

        # Update simple fields
        update_dict = rule_data.model_dump(exclude_unset=True)
        if "name" in update_dict or "is_active" in update_dict:
            for field in ["name", "is_active"]:
                if field in update_dict:
                    setattr(rule, field, update_dict[field])
            rule.updated_at = datetime.now(UTC)

        # Replace conditions if provided
        if rule_data.conditions is not None:
            # Delete existing conditions
            self.db_session.exec(
                delete(RuleCondition).where(RuleCondition.rule_id == rule_id)  # type: ignore
            )
            # Create new conditions with position assignment
            for position, condition_data in enumerate(rule_data.conditions):
                condition = RuleCondition(
                    rule_id=rule_id,
                    field=condition_data.field,
                    operator=condition_data.operator,
                    value=condition_data.value,
                    value_secondary=condition_data.value_secondary,
                    logical_operator=condition_data.logical_operator,
                    position=position,
                )
                self.db_session.add(condition)

        # Replace actions if provided
        if rule_data.actions is not None:
            # Delete existing actions
            self.db_session.exec(
                delete(RuleAction).where(RuleAction.rule_id == rule_id)  # type: ignore
            )
            # Create new actions
            for action_data in rule_data.actions:
                action = RuleAction(
                    rule_id=rule_id,
                    action_type=action_data.action_type,
                    tag_id=action_data.tag_id,
                )
                self.db_session.add(action)

        self.db_session.add(rule)
        self.db_session.commit()
        self.db_session.refresh(rule)
        return rule

    def delete(self, rule_id: uuid.UUID) -> None:
        """Delete a rule.

        Cascades to delete all associated conditions and actions.

        Args:
            rule_id: The ID of the rule to delete.

        Raises:
            RuleNotFoundError: If the rule is not found.
        """
        rule = self.get_by_id(rule_id)
        self.db_session.delete(rule)
        self.db_session.commit()


def provide(session: Session) -> RuleRepository:
    """Provide an instance of RuleRepository.

    Args:
        session: The database session to use.

    Returns:
        RuleRepository: An instance of RuleRepository with the given session.
    """
    return RuleRepository(session)
