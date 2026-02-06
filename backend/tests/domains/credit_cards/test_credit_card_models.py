"""Unit tests for CreditCard model fields."""

import json
import uuid
from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy import DECIMAL

from app.domains.credit_cards.domain.models import (
    CardBrand,
    CreditCard,
    CreditCardBase,
    CreditCardCreate,
    CreditCardPublic,
    CreditCardUpdate,
    LimitSource,
)


class TestLimitSource:
    """Tests for the LimitSource enum."""

    def test_limit_source_values(self):
        """LimitSource should have manual and statement values."""
        assert LimitSource.MANUAL == "manual"
        assert LimitSource.STATEMENT == "statement"


class TestCreditCardLimitFields:
    """Tests for the credit limit fields on CreditCard models."""

    def test_credit_card_defaults_to_none(self):
        """CreditCard table model should default limit fields to None."""
        card = CreditCard(
            user_id=uuid.uuid4(),
            bank="Test Bank",
            brand=CardBrand.VISA,
            last4="1234",
        )
        assert card.credit_limit is None
        assert card.limit_last_updated_at is None
        assert card.limit_source is None

    def test_credit_card_public_has_limit_fields(self):
        """CreditCardPublic should have limit fields."""
        card_id = uuid.uuid4()
        user_id = uuid.uuid4()
        card_public = CreditCardPublic(
            id=card_id,
            user_id=user_id,
            bank="Test Bank",
            brand=CardBrand.VISA,
            last4="1234",
            credit_limit=Decimal("1000.00"),
            limit_source=LimitSource.MANUAL,
        )
        assert card_public.credit_limit == Decimal("1000.00")
        assert card_public.limit_source == LimitSource.MANUAL

    def test_credit_card_update_validation(self):
        """CreditCardUpdate should validate credit_limit is positive."""
        # Valid update
        update = CreditCardUpdate(credit_limit=Decimal("1000.50"))
        assert update.credit_limit == Decimal("1000.50")

        # Invalid update: zero
        with pytest.raises(ValidationError):
            CreditCardUpdate(credit_limit=Decimal("0"))

        # Invalid update: negative
        with pytest.raises(ValidationError):
            CreditCardUpdate(credit_limit=Decimal("-100.00"))

    def test_credit_limit_precision_and_scale(self):
        """CreditCard.credit_limit should have DECIMAL(32, 2) precision/scale."""
        # Check CreditCard table model
        sa_col = CreditCard.model_fields["credit_limit"].sa_column
        assert isinstance(sa_col.type, DECIMAL)
        assert sa_col.type.precision == 32
        assert sa_col.type.scale == 2

    def test_credit_card_serialization(self):
        """CreditCardPublic should serialize credit limit fields to JSON."""
        card_public = CreditCardPublic(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            bank="Test Bank",
            brand=CardBrand.VISA,
            last4="1234",
            credit_limit=Decimal("5000.00"),
            limit_source=LimitSource.STATEMENT,
        )
        json_data = json.loads(card_public.model_dump_json())
        assert json_data["credit_limit"] == "5000.00"
        assert json_data["limit_source"] == "statement"
        assert "limit_last_updated_at" in json_data


class TestCreditCardDefaultCurrency:
    """Tests for the default_currency field on CreditCard."""

    def test_default_currency_defaults_to_ars(self):
        """CreditCard should default to ARS currency."""
        card = CreditCardBase(
            user_id=uuid.uuid4(),
            bank="Test Bank",
            brand=CardBrand.VISA,
            last4="1234",
        )
        assert card.default_currency == "ARS"

    def test_default_currency_can_be_customized(self):
        """CreditCard should accept custom currency."""
        card = CreditCardBase(
            user_id=uuid.uuid4(),
            bank="Test Bank",
            brand=CardBrand.VISA,
            last4="1234",
            default_currency="USD",
        )
        assert card.default_currency == "USD"

    def test_credit_card_create_inherits_default_currency(self):
        """CreditCardCreate should have default_currency field."""
        card = CreditCardCreate(
            user_id=uuid.uuid4(),
            bank="Test Bank",
            brand=CardBrand.VISA,
            last4="1234",
        )
        assert card.default_currency == "ARS"

    def test_credit_card_update_has_optional_default_currency(self):
        """CreditCardUpdate should have optional default_currency field."""
        update = CreditCardUpdate()
        assert update.default_currency is None

        update_with_currency = CreditCardUpdate(default_currency="EUR")
        assert update_with_currency.default_currency == "EUR"

    def test_credit_card_table_model_has_default_currency(self):
        """CreditCard table model should have default_currency field."""
        card = CreditCard(
            user_id=uuid.uuid4(),
            bank="Test Bank",
            brand=CardBrand.VISA,
            last4="1234",
        )
        assert card.default_currency == "ARS"


class TestCreditCardAlias:
    """Tests for the alias field on CreditCard."""

    def test_alias_defaults_to_none(self):
        """CreditCard should default alias to None."""
        card = CreditCardBase(
            user_id=uuid.uuid4(),
            bank="Test Bank",
            brand=CardBrand.VISA,
            last4="1234",
        )
        assert card.alias is None

    def test_alias_can_be_set(self):
        """CreditCard should accept custom alias."""
        card = CreditCardBase(
            user_id=uuid.uuid4(),
            bank="Test Bank",
            brand=CardBrand.VISA,
            last4="1234",
            alias="Personal Card",
        )
        assert card.alias == "Personal Card"

    def test_credit_card_create_has_optional_alias(self):
        """CreditCardCreate should have optional alias field."""
        card_without_alias = CreditCardCreate(
            user_id=uuid.uuid4(),
            bank="Test Bank",
            brand=CardBrand.VISA,
            last4="1234",
        )
        assert card_without_alias.alias is None

        card_with_alias = CreditCardCreate(
            user_id=uuid.uuid4(),
            bank="Test Bank",
            brand=CardBrand.VISA,
            last4="1234",
            alias="Work Card",
        )
        assert card_with_alias.alias == "Work Card"

    def test_credit_card_update_has_optional_alias(self):
        """CreditCardUpdate should have optional alias field."""
        update = CreditCardUpdate()
        assert update.alias is None

        update_with_alias = CreditCardUpdate(alias="Travel Card")
        assert update_with_alias.alias == "Travel Card"

    def test_credit_card_table_model_has_alias(self):
        """CreditCard table model should have alias field."""
        card = CreditCard(
            user_id=uuid.uuid4(),
            bank="Test Bank",
            brand=CardBrand.VISA,
            last4="1234",
            alias="Test Alias",
        )
        assert card.alias == "Test Alias"
