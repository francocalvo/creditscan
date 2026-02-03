"""Tests for RuleService."""

import uuid

import pytest
from sqlmodel import Session

from app.domains.rules.domain.errors import (
    RuleNotFoundError,
    RuleValidationError,
    TagNotFoundForActionError,
)
from app.domains.rules.domain.models import (
    ActionType,
    ConditionField,
    ConditionOperator,
    LogicalOperator,
    RuleActionCreate,
    RuleConditionCreate,
    RuleCreate,
    RuleUpdate,
)
from app.domains.rules.service.rule_service import RuleService
from app.domains.tags.domain.models import TagCreate
from app.domains.tags.repository.tag_repository import TagRepository
from app.domains.users.repository import UserRepository
from app.models import User, UserCreate

from ...utils.utils import random_email, random_lower_string


def create_test_user(db: Session) -> User:
    """Create a test user for rule tests."""
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = UserRepository(db).create(user_in)
    return user


def create_test_tag(
    db: Session, user_id: uuid.UUID, label: str = "test-tag"
) -> uuid.UUID:
    """Create a test tag and return its ID."""
    tag_in = TagCreate(user_id=user_id, label=label)
    tag = TagRepository(db).create(tag_in)
    return tag.tag_id


def get_service(db: Session) -> RuleService:
    """Get a RuleService instance."""
    from app.domains.rules.service import provide_rule_service

    return provide_rule_service(db)


def create_valid_rule_data(tag_id: uuid.UUID, name: str = "Test Rule") -> RuleCreate:
    """Create valid rule data with one condition and one action."""
    return RuleCreate(
        name=name,
        is_active=True,
        conditions=[
            RuleConditionCreate(
                field=ConditionField.PAYEE,
                operator=ConditionOperator.CONTAINS,
                value="amazon",
            )
        ],
        actions=[
            RuleActionCreate(
                action_type=ActionType.ADD_TAG,
                tag_id=tag_id,
            )
        ],
    )


class TestCreateRule:
    """Tests for creating rules."""

    def test_create_rule_success(self, db: Session) -> None:
        """Test creating a valid rule succeeds."""
        user = create_test_user(db)
        tag_id = create_test_tag(db, user.id)
        service = get_service(db)

        rule_data = create_valid_rule_data(tag_id)
        rule = service.create_rule(rule_data, user.id)

        assert rule.name == "Test Rule"
        assert rule.is_active is True
        assert rule.user_id == user.id
        assert len(rule.conditions) == 1
        assert len(rule.actions) == 1
        assert rule.conditions[0].field == ConditionField.PAYEE
        assert rule.actions[0].tag_id == tag_id

    def test_create_rule_missing_conditions_raises_error(self, db: Session) -> None:
        """Test creating a rule without conditions raises error."""
        user = create_test_user(db)
        tag_id = create_test_tag(db, user.id)
        service = get_service(db)

        rule_data = RuleCreate(
            name="No Conditions Rule",
            conditions=[],  # Empty conditions
            actions=[RuleActionCreate(action_type=ActionType.ADD_TAG, tag_id=tag_id)],
        )

        with pytest.raises(RuleValidationError, match="at least one condition"):
            service.create_rule(rule_data, user.id)

    def test_create_rule_missing_actions_raises_error(self, db: Session) -> None:
        """Test creating a rule without actions raises error."""
        user = create_test_user(db)
        service = get_service(db)

        rule_data = RuleCreate(
            name="No Actions Rule",
            conditions=[
                RuleConditionCreate(
                    field=ConditionField.PAYEE,
                    operator=ConditionOperator.CONTAINS,
                    value="test",
                )
            ],
            actions=[],  # Empty actions
        )

        with pytest.raises(RuleValidationError, match="at least one action"):
            service.create_rule(rule_data, user.id)

    def test_create_rule_invalid_tag_raises_error(self, db: Session) -> None:
        """Test creating a rule with non-existent tag raises error."""
        user = create_test_user(db)
        service = get_service(db)
        fake_tag_id = uuid.uuid4()

        rule_data = RuleCreate(
            name="Invalid Tag Rule",
            conditions=[
                RuleConditionCreate(
                    field=ConditionField.PAYEE,
                    operator=ConditionOperator.CONTAINS,
                    value="test",
                )
            ],
            actions=[
                RuleActionCreate(action_type=ActionType.ADD_TAG, tag_id=fake_tag_id)
            ],
        )

        with pytest.raises(TagNotFoundForActionError):
            service.create_rule(rule_data, user.id)

    def test_create_rule_soft_deleted_tag_raises_error(self, db: Session) -> None:
        """Test creating a rule with soft-deleted tag raises error."""
        user = create_test_user(db)
        tag_id = create_test_tag(db, user.id)
        # Soft delete the tag
        TagRepository(db).delete(tag_id)

        service = get_service(db)

        rule_data = RuleCreate(
            name="Deleted Tag Rule",
            conditions=[
                RuleConditionCreate(
                    field=ConditionField.PAYEE,
                    operator=ConditionOperator.CONTAINS,
                    value="test",
                )
            ],
            actions=[RuleActionCreate(action_type=ActionType.ADD_TAG, tag_id=tag_id)],
        )

        with pytest.raises(TagNotFoundForActionError):
            service.create_rule(rule_data, user.id)

    def test_create_rule_multiple_conditions(self, db: Session) -> None:
        """Test creating a rule with multiple conditions."""
        user = create_test_user(db)
        tag_id = create_test_tag(db, user.id)
        service = get_service(db)

        rule_data = RuleCreate(
            name="Multi-Condition Rule",
            conditions=[
                RuleConditionCreate(
                    field=ConditionField.PAYEE,
                    operator=ConditionOperator.CONTAINS,
                    value="amazon",
                ),
                RuleConditionCreate(
                    field=ConditionField.AMOUNT,
                    operator=ConditionOperator.GT,
                    value="50.00",
                    logical_operator=LogicalOperator.AND,
                ),
            ],
            actions=[RuleActionCreate(action_type=ActionType.ADD_TAG, tag_id=tag_id)],
        )

        rule = service.create_rule(rule_data, user.id)
        assert len(rule.conditions) == 2


class TestGetRule:
    """Tests for getting rules."""

    def test_get_rule_success(self, db: Session) -> None:
        """Test getting a rule by ID succeeds."""
        user = create_test_user(db)
        tag_id = create_test_tag(db, user.id)
        service = get_service(db)

        rule_data = create_valid_rule_data(tag_id)
        created = service.create_rule(rule_data, user.id)

        retrieved = service.get_rule(created.rule_id, user.id)
        assert retrieved.rule_id == created.rule_id
        assert retrieved.name == created.name

    def test_get_rule_not_found_raises_error(self, db: Session) -> None:
        """Test getting a non-existent rule raises error."""
        user = create_test_user(db)
        service = get_service(db)

        with pytest.raises(RuleNotFoundError):
            service.get_rule(uuid.uuid4(), user.id)

    def test_get_rule_wrong_user_raises_not_found(self, db: Session) -> None:
        """Test getting another user's rule raises RuleNotFoundError."""
        user1 = create_test_user(db)
        user2 = create_test_user(db)
        tag_id = create_test_tag(db, user1.id)
        service = get_service(db)

        rule_data = create_valid_rule_data(tag_id)
        created = service.create_rule(rule_data, user1.id)

        # User2 tries to access User1's rule
        with pytest.raises(RuleNotFoundError):
            service.get_rule(created.rule_id, user2.id)


class TestListRules:
    """Tests for listing rules."""

    def test_list_rules_returns_only_user_rules(self, db: Session) -> None:
        """Test listing rules only returns the user's own rules."""
        user1 = create_test_user(db)
        user2 = create_test_user(db)
        tag1_id = create_test_tag(db, user1.id, "tag1")
        tag2_id = create_test_tag(db, user2.id, "tag2")
        service = get_service(db)

        # Create rules for both users
        service.create_rule(create_valid_rule_data(tag1_id, "User1 Rule"), user1.id)
        service.create_rule(create_valid_rule_data(tag2_id, "User2 Rule"), user2.id)

        # List rules for user1
        result = service.list_rules(user1.id)
        assert result.count == 1
        assert len(result.data) == 1
        assert result.data[0].name == "User1 Rule"

        # List rules for user2
        result = service.list_rules(user2.id)
        assert result.count == 1
        assert result.data[0].name == "User2 Rule"

    def test_list_rules_pagination(self, db: Session) -> None:
        """Test pagination works correctly."""
        user = create_test_user(db)
        tag_id = create_test_tag(db, user.id)
        service = get_service(db)

        # Create 5 rules
        for i in range(5):
            service.create_rule(create_valid_rule_data(tag_id, f"Rule {i}"), user.id)

        # Get first page
        result = service.list_rules(user.id, skip=0, limit=2)
        assert result.count == 5
        assert len(result.data) == 2

        # Get second page
        result = service.list_rules(user.id, skip=2, limit=2)
        assert result.count == 5
        assert len(result.data) == 2

        # Get last page
        result = service.list_rules(user.id, skip=4, limit=2)
        assert result.count == 5
        assert len(result.data) == 1


class TestUpdateRule:
    """Tests for updating rules."""

    def test_update_rule_success(self, db: Session) -> None:
        """Test updating a rule succeeds."""
        user = create_test_user(db)
        tag_id = create_test_tag(db, user.id)
        service = get_service(db)

        rule_data = create_valid_rule_data(tag_id)
        created = service.create_rule(rule_data, user.id)

        update_data = RuleUpdate(name="Updated Name", is_active=False)
        updated = service.update_rule(created.rule_id, user.id, update_data)

        assert updated.name == "Updated Name"
        assert updated.is_active is False
        assert updated.updated_at is not None

    def test_update_rule_conditions(self, db: Session) -> None:
        """Test updating a rule's conditions."""
        user = create_test_user(db)
        tag_id = create_test_tag(db, user.id)
        service = get_service(db)

        rule_data = create_valid_rule_data(tag_id)
        created = service.create_rule(rule_data, user.id)

        # Update with new conditions
        update_data = RuleUpdate(
            conditions=[
                RuleConditionCreate(
                    field=ConditionField.DESCRIPTION,
                    operator=ConditionOperator.CONTAINS,
                    value="new condition",
                )
            ]
        )
        updated = service.update_rule(created.rule_id, user.id, update_data)

        assert len(updated.conditions) == 1
        assert updated.conditions[0].field == ConditionField.DESCRIPTION

    def test_update_rule_empty_conditions_raises_error(self, db: Session) -> None:
        """Test updating with empty conditions raises error."""
        user = create_test_user(db)
        tag_id = create_test_tag(db, user.id)
        service = get_service(db)

        rule_data = create_valid_rule_data(tag_id)
        created = service.create_rule(rule_data, user.id)

        update_data = RuleUpdate(conditions=[])
        with pytest.raises(RuleValidationError, match="at least one condition"):
            service.update_rule(created.rule_id, user.id, update_data)

    def test_update_rule_empty_actions_raises_error(self, db: Session) -> None:
        """Test updating with empty actions raises error."""
        user = create_test_user(db)
        tag_id = create_test_tag(db, user.id)
        service = get_service(db)

        rule_data = create_valid_rule_data(tag_id)
        created = service.create_rule(rule_data, user.id)

        update_data = RuleUpdate(actions=[])
        with pytest.raises(RuleValidationError, match="at least one action"):
            service.update_rule(created.rule_id, user.id, update_data)

    def test_update_rule_wrong_user_raises_not_found(self, db: Session) -> None:
        """Test updating another user's rule raises RuleNotFoundError."""
        user1 = create_test_user(db)
        user2 = create_test_user(db)
        tag_id = create_test_tag(db, user1.id)
        service = get_service(db)

        rule_data = create_valid_rule_data(tag_id)
        created = service.create_rule(rule_data, user1.id)

        update_data = RuleUpdate(name="Hacked Name")
        with pytest.raises(RuleNotFoundError):
            service.update_rule(created.rule_id, user2.id, update_data)


class TestDeleteRule:
    """Tests for deleting rules."""

    def test_delete_rule_success(self, db: Session) -> None:
        """Test deleting a rule succeeds."""
        user = create_test_user(db)
        tag_id = create_test_tag(db, user.id)
        service = get_service(db)

        rule_data = create_valid_rule_data(tag_id)
        created = service.create_rule(rule_data, user.id)

        service.delete_rule(created.rule_id, user.id)

        # Verify it's deleted
        with pytest.raises(RuleNotFoundError):
            service.get_rule(created.rule_id, user.id)

    def test_delete_rule_wrong_user_raises_not_found(self, db: Session) -> None:
        """Test deleting another user's rule raises RuleNotFoundError."""
        user1 = create_test_user(db)
        user2 = create_test_user(db)
        tag_id = create_test_tag(db, user1.id)
        service = get_service(db)

        rule_data = create_valid_rule_data(tag_id)
        created = service.create_rule(rule_data, user1.id)

        with pytest.raises(RuleNotFoundError):
            service.delete_rule(created.rule_id, user2.id)

        # Verify it still exists for user1
        rule = service.get_rule(created.rule_id, user1.id)
        assert rule is not None
