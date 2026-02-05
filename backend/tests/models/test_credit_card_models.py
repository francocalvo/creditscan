"""Unit tests for CreditCard model fields."""

import uuid

from app.domains.credit_cards.domain.models import (
    CardBrand,
    CreditCard,
    CreditCardBase,
    CreditCardCreate,
    CreditCardUpdate,
)


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
