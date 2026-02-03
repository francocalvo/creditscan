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
