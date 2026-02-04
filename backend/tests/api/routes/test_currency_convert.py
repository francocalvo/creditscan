"""Tests for currency conversion endpoints."""

from decimal import Decimal

from fastapi.testclient import TestClient

from app.core.config import settings


class TestCurrencyConvert:
    """Tests for POST /currency/convert and /currency/convert/batch."""

    def test_convert_requires_auth(self, client: TestClient) -> None:
        """Unauthenticated requests should be rejected."""
        r = client.post(
            f"{settings.API_V1_STR}/currency/convert",
            json={"amount": 100, "from_currency": "USD", "to_currency": "ARS"},
        )
        assert r.status_code == 401

    def test_convert_same_currency(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        """Same currency should return the original amount with rate 1."""
        r = client.post(
            f"{settings.API_V1_STR}/currency/convert",
            headers=normal_user_token_headers,
            json={"amount": 100, "from_currency": "USD", "to_currency": "USD"},
        )
        assert r.status_code == 200
        body = r.json()

        assert Decimal(str(body["original_amount"])) == Decimal("100")
        assert Decimal(str(body["converted_amount"])) == Decimal("100.00")
        assert body["from_currency"] == "USD"
        assert body["to_currency"] == "USD"
        assert Decimal(str(body["rate"])) == Decimal("1")

    def test_convert_usd_to_ars(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        """USD->ARS should use the static rate table."""
        r = client.post(
            f"{settings.API_V1_STR}/currency/convert",
            headers=normal_user_token_headers,
            json={"amount": 100, "from_currency": "USD", "to_currency": "ARS"},
        )
        assert r.status_code == 200
        body = r.json()

        assert Decimal(str(body["converted_amount"])) == Decimal("100000.00")
        assert Decimal(str(body["rate"])) == Decimal("1000")

    def test_convert_batch(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        """Batch conversion should return results in order."""
        r = client.post(
            f"{settings.API_V1_STR}/currency/convert/batch",
            headers=normal_user_token_headers,
            json={
                "conversions": [
                    {"amount": 10, "from_currency": "USD", "to_currency": "ARS"},
                    {"amount": 1000, "from_currency": "ARS", "to_currency": "USD"},
                ]
            },
        )
        assert r.status_code == 200
        body = r.json()

        assert "results" in body
        assert len(body["results"]) == 2
        assert Decimal(str(body["results"][0]["converted_amount"])) == Decimal(
            "10000.00"
        )
        assert Decimal(str(body["results"][1]["converted_amount"])) == Decimal("1.00")

    def test_convert_unsupported_currency_returns_400(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        """Unsupported currency codes should return a 400 error."""
        r = client.post(
            f"{settings.API_V1_STR}/currency/convert",
            headers=normal_user_token_headers,
            json={"amount": 100, "from_currency": "USD", "to_currency": "XXX"},
        )
        assert r.status_code == 400
        assert "unsupported currency" in r.json()["detail"].lower()

    def test_convert_invalid_currency_format_returns_422(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        """Invalid currency code format should return a 422 validation error."""
        r = client.post(
            f"{settings.API_V1_STR}/currency/convert",
            headers=normal_user_token_headers,
            json={"amount": 100, "from_currency": "US1", "to_currency": "USD"},
        )
        assert r.status_code == 422
