"""Tests for rules CRUD API endpoints."""

import uuid

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
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """Test that users can only see their own rules."""
    user = create_test_user(db)
    tag = create_test_tag(db, user.id)

    # Create a rule for the test user (authenticated via normal_user_token_headers)
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

    # Create rule with authenticated user's token
    create_r = client.post(
        f"{settings.API_V1_STR}/rules/",
        headers=normal_user_token_headers,
        json=rule_data.model_dump(mode="json"),
    )
    assert create_r.status_code == 201
    rule_id = create_r.json()["rule_id"]

    # List rules with authenticated user - should see the rule we created
    r = client.get(
        f"{settings.API_V1_STR}/rules/",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 200
    result = RulesPublic(**r.json())
    assert result.count == 1
    assert len(result.data) == 1
    assert result.data[0].rule_id == uuid.UUID(rule_id)


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
    assert str(rule.rule_id) == rule_id
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
    # Create a different user and tag for them
    user = create_test_user(db)
    tag = create_test_tag(db, user.id)

    # We'll create rule via direct DB insert since we can't authenticate as other user
    from datetime import datetime, timezone

    from app.domains.rules.domain.models import Rule, RuleAction, RuleCondition

    rule = Rule(
        user_id=user.id,
        name="Other User Rule",
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(rule)
    db.flush()

    condition = RuleCondition(
        rule_id=rule.rule_id,
        field=ConditionField.PAYEE,
        operator=ConditionOperator.CONTAINS,
        value="amazon",
        logical_operator=LogicalOperator.AND,
        position=0,
    )
    db.add(condition)

    action = RuleAction(
        rule_id=rule.rule_id,
        action_type=ActionType.ADD_TAG,
        tag_id=tag.tag_id,
    )
    db.add(action)
    db.commit()

    # Try to get rule as normal user - should fail with 404
    r = client.get(
        f"{settings.API_V1_STR}/rules/{rule.rule_id}",
        headers=normal_user_token_headers,
    )

    # Should return 404 since rule belongs to different user
    assert r.status_code == 404
    assert "not found" in r.json()["detail"]


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
