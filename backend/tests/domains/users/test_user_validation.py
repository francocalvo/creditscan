"""Tests for user model validation."""

import pytest
from pydantic import ValidationError

from app.domains.users.domain.models import UserBase, UserUpdateMe


class TestNtfyTopicValidation:
    def test_valid_alphanumeric(self) -> None:
        user = UserBase(
            email="test@example.com",
            ntfy_topic="my-topic-123",
        )
        assert user.ntfy_topic == "my-topic-123"

    def test_valid_with_underscores(self) -> None:
        user = UserBase(
            email="test@example.com",
            ntfy_topic="pf_app_abc123",
        )
        assert user.ntfy_topic == "pf_app_abc123"

    def test_valid_none(self) -> None:
        user = UserBase(
            email="test@example.com",
            ntfy_topic=None,
        )
        assert user.ntfy_topic is None

    def test_invalid_spaces(self) -> None:
        with pytest.raises(ValidationError, match="ntfy_topic"):
            UserBase(
                email="test@example.com",
                ntfy_topic="my topic",
            )

    def test_invalid_special_chars(self) -> None:
        with pytest.raises(ValidationError, match="ntfy_topic"):
            UserBase(
                email="test@example.com",
                ntfy_topic="my@topic#123",
            )

    def test_invalid_slashes(self) -> None:
        with pytest.raises(ValidationError, match="ntfy_topic"):
            UserBase(
                email="test@example.com",
                ntfy_topic="path/to/topic",
            )

    def test_update_me_valid(self) -> None:
        update = UserUpdateMe(ntfy_topic="valid-topic")
        assert update.ntfy_topic == "valid-topic"

    def test_update_me_invalid(self) -> None:
        with pytest.raises(ValidationError, match="ntfy_topic"):
            UserUpdateMe(ntfy_topic="invalid topic!")
