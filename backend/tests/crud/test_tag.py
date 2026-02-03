"""Tests for TagRepository soft-delete functionality."""

from datetime import datetime

import pytest
from sqlmodel import Session

from app.domains.tags.domain.errors import TagNotFoundError
from app.domains.tags.domain.models import Tag, TagCreate, TagUpdate
from app.domains.tags.repository.tag_repository import TagRepository
from app.domains.users.repository import UserRepository
from app.models import User, UserCreate

from ..utils.utils import random_email, random_lower_string


def create_test_user(db: Session) -> User:
    """Create a test user for tag tests.

    Tags require a user_id foreign key, so we need to create a user first.
    """
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = UserRepository(db).create(user_in)
    return user


def test_delete_tag_sets_deleted_at_timestamp(db: Session) -> None:
    """Verify soft delete sets the deleted_at timestamp."""
    user = create_test_user(db)
    tag_in = TagCreate(user_id=user.id, label="test-tag")
    tag = TagRepository(db).create(tag_in)

    # Delete the tag (soft delete)
    TagRepository(db).delete(tag.tag_id)

    # Verify deleted_at is set by querying database directly
    deleted_tag = db.get(Tag, tag.tag_id)
    assert deleted_tag is not None
    assert deleted_tag.deleted_at is not None
    assert isinstance(deleted_tag.deleted_at, datetime)
    # Should be recent (within last minute)
    assert deleted_tag.deleted_at > datetime.utcnow().replace(second=0, microsecond=0)


def test_list_excludes_deleted_tags(db: Session) -> None:
    """Verify list() does not return soft-deleted tags."""
    user = create_test_user(db)

    # Create two tags
    active_tag_in = TagCreate(user_id=user.id, label="active-tag")
    active_tag = TagRepository(db).create(active_tag_in)

    deleted_tag_in = TagCreate(user_id=user.id, label="deleted-tag")
    deleted_tag = TagRepository(db).create(deleted_tag_in)

    # Delete one tag
    TagRepository(db).delete(deleted_tag.tag_id)

    # List tags
    tags = TagRepository(db).list(filters={"user_id": user.id})

    # Only active tag should be in results
    tag_ids = [tag.tag_id for tag in tags]
    assert active_tag.tag_id in tag_ids
    assert deleted_tag.tag_id not in tag_ids
    assert len(tags) == 1


def test_get_by_id_excludes_deleted_tags_by_default(db: Session) -> None:
    """Verify get_by_id() raises TagNotFoundError for deleted tags."""
    user = create_test_user(db)
    tag_in = TagCreate(user_id=user.id, label="test-tag")
    tag = TagRepository(db).create(tag_in)

    # Delete the tag
    TagRepository(db).delete(tag.tag_id)

    # Try to get it with default include_deleted=False
    with pytest.raises(TagNotFoundError):
        TagRepository(db).get_by_id(tag.tag_id)


def test_get_by_id_with_include_deleted_returns_deleted_tags(db: Session) -> None:
    """Verify get_by_id(include_deleted=True) returns deleted tags."""
    user = create_test_user(db)
    tag_in = TagCreate(user_id=user.id, label="test-tag")
    tag = TagRepository(db).create(tag_in)

    # Delete the tag
    TagRepository(db).delete(tag.tag_id)

    # Get it with include_deleted=True
    retrieved_tag = TagRepository(db).get_by_id(tag.tag_id, include_deleted=True)

    # Tag should be returned
    assert retrieved_tag is not None
    assert retrieved_tag.tag_id == tag.tag_id
    assert retrieved_tag.deleted_at is not None


def test_count_excludes_deleted_tags(db: Session) -> None:
    """Verify count() does not count soft-deleted tags."""
    user = create_test_user(db)

    # Create three tags
    TagRepository(db).create(TagCreate(user_id=user.id, label="tag1"))
    tag_to_delete = TagRepository(db).create(TagCreate(user_id=user.id, label="tag2"))
    TagRepository(db).create(TagCreate(user_id=user.id, label="tag3"))

    # Delete one tag
    TagRepository(db).delete(tag_to_delete.tag_id)

    # Count tags
    count = TagRepository(db).count(filters={"user_id": user.id})

    # Should count only 2 (not 3)
    assert count == 2


def test_delete_already_deleted_tag_raises_error(db: Session) -> None:
    """Verify double-delete fails (can't delete already-deleted tag)."""
    user = create_test_user(db)
    tag_in = TagCreate(user_id=user.id, label="test-tag")
    tag = TagRepository(db).create(tag_in)

    # First delete
    TagRepository(db).delete(tag.tag_id)

    # Try to delete again - should raise TagNotFoundError
    with pytest.raises(TagNotFoundError):
        TagRepository(db).delete(tag.tag_id)


def test_update_deleted_tag_raises_error(db: Session) -> None:
    """Verify updating a deleted tag fails."""
    user = create_test_user(db)
    tag_in = TagCreate(user_id=user.id, label="original-label")
    tag = TagRepository(db).create(tag_in)

    # Delete the tag
    TagRepository(db).delete(tag.tag_id)

    # Try to update it - should raise TagNotFoundError
    with pytest.raises(TagNotFoundError):
        TagRepository(db).update(tag.tag_id, TagUpdate(label="new-label"))
