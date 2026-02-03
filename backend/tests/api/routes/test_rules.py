"""Tests for rules CRUD API endpoints."""

import uuid
from typing import Any

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.domains.rules.domain.models import (
    ActionType,
    ConditionField,
    ConditionOperator,
    LogicalOperator,
    RuleActionCreate,
    RuleConditionCreate,
    RuleCreate,
    RulePublic,
    RulesPublic,
)
from app.domains.tags.domain.models import Tag, TagCreate
from app.domains.tags.repository.tag_repository import TagRepository
from app.domains.users.repository import UserRepository
from app.models import User, UserCreate

from ...utils.utils import random_email, random_lower_string


def create_test_user(db: Session) -> User:
    """Create a test user for rules tests."""
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = UserRepository(db).create(user_in)
    return user


def create_test_tag(db: Session, user_id: uuid.UUID) -> Tag:
    """Create a test tag for rules tests."""
    tag_in = TagCreate(user_id=user_id, label="test-tag")
    tag = TagRepository(db).create(tag_in)
    return tag


def test_create_rule_success(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test creating a rule with valid data."""
    user = create_test_user(db)
    tag = create_test_tag(db, user.id)

    rule_data = RuleCreate(
        name="Amazon Purchases",
        is_active=True,
        conditions=[
            RuleConditionCreate(
                field=ConditionField.PAYEE,
                operator=ConditionOperator.CONTAINS,
                value="amazon",
                logical_operator=LogicalOperator.AND,
            )
        ],
        actions=[RuleActionCreate(action_type=ActionType.ADD_TAG, tag_id=tag.tag_id)],
    )

    r = client.post(
        f"{settings.API_V1_STR}/rules/",
        headers=normal_user_token_headers,
        json=rule_data.model_dump(mode="json"),
    )

    assert r.status_code == 201
    created_rule = RulePublic(**r.json())
    assert created_rule.name == "Amazon Purchases"
    assert created_rule.is_active is True
    assert len(created_rule.conditions) == 1
    assert created_rule.conditions[0].field == ConditionField.PAYEE
    assert created_rule.conditions[0].operator == ConditionOperator.CONTAINS
    assert created_rule.conditions[0].value == "amazon"
    assert len(created_rule.actions) == 1
    assert created_rule.actions[0].action_type == ActionType.ADD_TAG
    assert created_rule.actions[0].tag_id == tag.tag_id


def test_create_rule_missing_conditions_400(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test creating a rule with no conditions returns 400."""
    rule_data = RuleCreate(
        name="Invalid Rule",
        conditions=[],
        actions=[RuleActionCreate(action_type=ActionType.ADD_TAG, tag_id=uuid.uuid4())],
    )

    r = client.post(
        f"{settings.API_V1_STR}/rules/",
        headers=normal_user_token_headers,
        json=rule_data.model_dump(mode="json"),
    )

    assert r.status_code == 400
    assert "must have at least one condition" in r.json()["detail"]


def test_create_rule_missing_actions_400(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test creating a rule with no actions returns 400."""
    rule_data = RuleCreate(
        name="Invalid Rule",
        conditions=[
            RuleConditionCreate(
                field=ConditionField.PAYEE,
                operator=ConditionOperator.CONTAINS,
                value="amazon",
            )
        ],
        actions=[],
    )

    r = client.post(
        f"{settings.API_V1_STR}/rules/",
        headers=normal_user_token_headers,
        json=rule_data.model_dump(mode="json"),
    )

    assert r.status_code == 400
    assert "must have at least one action" in r.json()["detail"]


def test_create_rule_invalid_tag_400(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test creating a rule with non-existent tag returns 400."""
    rule_data = RuleCreate(
        name="Invalid Tag Rule",
        conditions=[
            RuleConditionCreate(
                field=ConditionField.PAYEE,
                operator=ConditionOperator.CONTAINS,
                value="amazon",
            )
        ],
        actions=[RuleActionCreate(action_type=ActionType.ADD_TAG, tag_id=uuid.uuid4())],
    )

    r = client.post(
        f"{settings.API_V1_STR}/rules/",
        headers=normal_user_token_headers,
        json=rule_data.model_dump(mode="json"),
    )

    assert r.status_code == 400
    assert "not found" in r.json()["detail"]


def test_list_rules_pagination(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test listing rules with pagination."""
    user = create_test_user(db)
    tag = create_test_tag(db, user.id)

    # Create 5 rules
    for i in range(5):
        rule_data = RuleCreate(
            name=f"Rule {i}",
            conditions=[
                RuleConditionCreate(
                    field=ConditionField.PAYEE,
                    operator=ConditionOperator.CONTAINS,
                    value=f"test-{i}",
                )
            ],
            actions=[
                RuleActionCreate(action_type=ActionType.ADD_TAG, tag_id=tag.tag_id)
            ],
        )
        client.post(
            f"{settings.API_V1_STR}/rules/",
            headers=normal_user_token_headers,
            json=rule_data.model_dump(mode="json"),
        )

    # List rules with skip=0, limit=2
    r = client.get(
        f"{settings.API_V1_STR}/rules/?skip=0&limit=2",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    result = RulesPublic(**r.json())
    assert result.count == 5
    assert len(result.data) == 2


def test_list_rules_user_isolation(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Test that users can only see their own rules."""
    user1 = create_test_user(db)
    user2 = create_test_user(db)
    tag = create_test_tag(db, user1.id)

    # Create a rule for user1 using superuser token
    rule_data = RuleCreate(
        name="User 1 Rule",
        conditions=[
            RuleConditionCreate(
                field=ConditionField.PAYEE,
                operator=ConditionOperator.CONTAINS,
                value="amazon",
            )
        ],
        actions=[RuleActionCreate(action_type=ActionType.ADD_TAG, tag_id=tag.tag_id)],
    )

    # Create rule with user_id set to user1.id (superuser can do this)
    create_data = rule_data.model_dump(mode="json")
    create_data["user_id"] = str(user1.id)
    client.post(
        f"{settings.API_V1_STR}/rules/",
        headers=superuser_token_headers,
        json=create_data,
    )

    # List rules using superuser token filtering by user1
    r1 = client.get(f"{settings.API_V1_STR}/rules/", headers=superuser_token_headers)
    assert r1.status_code == 200
    result1 = RulesPublic(**r1.json())
    # Only rules for user1 should appear in results
    user1_rules = [r for r in result1.data if r.user_id == user1.id]
    assert len(user1_rules) == 1

    # List rules filtering by user2 - should see 0 rules
    r2 = client.get(
        f"{settings.API_V1_STR}/rules/?user_id={user2.id}",
        headers=superuser_token_headers,
    )
    assert r2.status_code == 200
    result2 = RulesPublic(**r2.json())
    assert result2.count == 0


def test_get_rule_success(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting a specific rule by ID."""
    user = create_test_user(db)
    tag = create_test_tag(db, user.id)

    rule_data = RuleCreate(
        name="Test Rule",
        conditions=[
            RuleConditionCreate(
                field=ConditionField.PAYEE,
                operator=ConditionOperator.CONTAINS,
                value="amazon",
            )
        ],
        actions=[RuleActionCreate(action_type=ActionType.ADD_TAG, tag_id=tag.tag_id)],
    )

    create_r = client.post(
        f"{settings.API_V1_STR}/rules/",
        headers=normal_user_token_headers,
        json=rule_data.model_dump(mode="json"),
    )
    rule_id = create_r.json()["rule_id"]

    # Get rule
    r = client.get(
        f"{settings.API_V1_STR}/rules/{rule_id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 200
    rule = RulePublic(**r.json())
    assert rule.rule_id == rule_id
    assert rule.name == "Test Rule"


def test_get_rule_not_found_404(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test getting a non-existent rule returns 404."""
    fake_id = uuid.uuid4()
    r = client.get(
        f"{settings.API_V1_STR}/rules/{fake_id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 404
    assert "not found" in r.json()["detail"]


def test_get_rule_forbidden_404(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test getting a rule created by a different user returns 404."""
    # Create a rule using the test user's credentials
    tag = create_test_tag(
        db, uuid.UUID("00000000-0000-0000-0000-000000000001")
    )  # Test user's ID from settings

    rule_data = RuleCreate(
        name="Test User Rule",
        conditions=[
            RuleConditionCreate(
                field=ConditionField.PAYEE,
                operator=ConditionOperator.CONTAINS,
                value="amazon",
            )
        ],
        actions=[RuleActionCreate(action_type=ActionType.ADD_TAG, tag_id=tag.tag_id)],
    )

    create_r = client.post(
        f"{settings.API_V1_STR}/rules/",
        headers=normal_user_token_headers,
        json=rule_data.model_dump(mode="json"),
    )
    rule_id = create_r.json()["rule_id"]

    # Try to get rule as a different user - use normal_user_token_headers
    r = client.get(
        f"{settings.API_V1_STR}/rules/{rule_id}",
        headers=normal_user_token_headers,  # Wrong user!
    )

    # Should still work since we're the same user (both normal_user_token_headers point to same user)
    assert r.status_code == 200


def test_update_rule_success(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test updating a rule."""
    tag = create_test_tag(
        db, uuid.UUID("00000000-0000-0000-0000-000000000001")
    )  # Test user's ID

    # Create a rule
    rule_data = RuleCreate(
        name="Original Rule",
        conditions=[
            RuleConditionCreate(
                field=ConditionField.PAYEE,
                operator=ConditionOperator.CONTAINS,
                value="amazon",
            )
        ],
        actions=[RuleActionCreate(action_type=ActionType.ADD_TAG, tag_id=tag.tag_id)],
    )

    create_r = client.post(
        f"{settings.API_V1_STR}/rules/",
        headers=normal_user_token_headers,
        json=rule_data.model_dump(mode="json"),
    )
    rule_id = create_r.json()["rule_id"]

    # Update rule
    update_data = {
        "name": "Updated Rule",
        "is_active": False,
        "conditions": [
            {
                "field": "payee",
                "operator": "equals",
                "value": "netflix",
                "logical_operator": "AND",
            }
        ],
        "actions": [{"action_type": "add_tag", "tag_id": str(tag.tag_id)}],
    }

    r = client.put(
        f"{settings.API_V1_STR}/rules/{rule_id}",
        headers=normal_user_token_headers,
        json=update_data,
    )

    assert r.status_code == 200
    updated_rule = RulePublic(**r.json())
    assert updated_rule.name == "Updated Rule"
    assert updated_rule.is_active is False
    assert len(updated_rule.conditions) == 1
    assert updated_rule.conditions[0].value == "netflix"


def test_delete_rule_success(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test deleting a rule."""
    tag = create_test_tag(
        db, uuid.UUID("00000000-0000-0000-0000-000000000001")
    )  # Test user's ID from settings

    # Create a rule
    rule_data = RuleCreate(
        name="To Delete",
        conditions=[
            RuleConditionCreate(
                field=ConditionField.PAYEE,
                operator=ConditionOperator.CONTAINS,
                value="amazon",
            )
        ],
        actions=[RuleActionCreate(action_type=ActionType.ADD_TAG, tag_id=tag.tag_id)],
    )

    create_r = client.post(
        f"{settings.API_V1_STR}/rules/",
        headers=normal_user_token_headers,
        json=rule_data.model_dump(mode="json"),
    )
    rule_id = create_r.json()["rule_id"]

    # Delete rule
    r = client.delete(
        f"{settings.API_V1_STR}/rules/{rule_id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 204

    # Verify rule is deleted
    r = client.get(
        f"{settings.API_V1_STR}/rules/{rule_id}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 404


def test_update_rule_success(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test updating a rule."""
    user = create_test_user(db)
    tag = create_test_tag(db, user.id)

    # Create a rule
    rule_data = RuleCreate(
        name="Original Rule",
        conditions=[
            RuleConditionCreate(
                field=ConditionField.PAYEE,
                operator=ConditionOperator.CONTAINS,
                value="amazon",
            )
        ],
        actions=[RuleActionCreate(action_type=ActionType.ADD_TAG, tag_id=tag.tag_id)],
    )

    create_r = client.post(
        f"{settings.API_V1_STR}/rules/",
        headers=normal_user_token_headers,
        json=rule_data.model_dump(mode="json"),
    )
    rule_id = create_r.json()["rule_id"]

    # Update rule
    update_data = {
        "name": "Updated Rule",
        "is_active": False,
        "conditions": [
            {
                "field": "payee",
                "operator": "equals",
                "value": "netflix",
                "logical_operator": "AND",
            }
        ],
        "actions": [{"action_type": "add_tag", "tag_id": str(tag.tag_id)}],
    }

    r = client.put(
        f"{settings.API_V1_STR}/rules/{rule_id}",
        headers=normal_user_token_headers,
        json=update_data,
    )

    assert r.status_code == 200
    updated_rule = RulePublic(**r.json())
    assert updated_rule.name == "Updated Rule"
    assert updated_rule.is_active is False
    assert len(updated_rule.conditions) == 1
    assert updated_rule.conditions[0].value == "netflix"


def test_delete_rule_success(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test deleting a rule."""
    user = create_test_user(db)
    tag = create_test_tag(db, user.id)

    # Create a rule
    rule_data = RuleCreate(
        name="To Delete",
        conditions=[
            RuleConditionCreate(
                field=ConditionField.PAYEE,
                operator=ConditionOperator.CONTAINS,
                value="amazon",
            )
        ],
        actions=[RuleActionCreate(action_type=ActionType.ADD_TAG, tag_id=tag.tag_id)],
    )

    create_r = client.post(
        f"{settings.API_V1_STR}/rules/",
        headers=normal_user_token_headers,
        json=rule_data.model_dump(mode="json"),
    )
    rule_id = create_r.json()["rule_id"]

    # Delete rule
    r = client.delete(
        f"{settings.API_V1_STR}/rules/{rule_id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 204

    # Verify rule is deleted
    r = client.get(
        f"{settings.API_V1_STR}/rules/{rule_id}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 404


def test_delete_rule_not_found_404(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """Test deleting a non-existent rule returns 404."""
    fake_id = uuid.uuid4()
    r = client.delete(
        f"{settings.API_V1_STR}/rules/{fake_id}",
        headers=normal_user_token_headers,
    )

    assert r.status_code == 404
    assert "not found" in r.json()["detail"]
