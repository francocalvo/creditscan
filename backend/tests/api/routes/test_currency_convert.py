"""Tests for currency conversion endpoints."""

from datetime import date as Date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.domains.currency.domain.models import ExchangeRate


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
        """Same currency should return original amount with rate 1."""
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
        assert "rate_date" in body

    def test_convert_usd_to_ars_with_db_rate(
        self,
        client: TestClient,
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """USD->ARS should use database rates."""
        # Insert a test rate
        rate = ExchangeRate(
            buy_rate=Decimal("1458.74"),
            sell_rate=Decimal("1459.32"),
            rate_date=Date(2026, 2, 1),
        )
        db.add(rate)
        db.commit()

        r = client.post(
            f"{settings.API_V1_STR}/currency/convert",
            headers=normal_user_token_headers,
            json={
                "amount": 100,
                "from_currency": "USD",
                "to_currency": "ARS",
                "date": "2026-02-01",
            },
        )
        assert r.status_code == 200
        body = r.json()

        # Average rate: (1458.74 + 1459.32) / 2 = 1459.03
        # 100 USD * 1459.03 = 145903 ARS
        assert Decimal(str(body["converted_amount"])) == Decimal("145903.00")
        assert Decimal(str(body["rate"])) == Decimal("1459.03")
        assert body["rate_date"] == "2026-02-01"

    def test_convert_ars_to_usd_with_db_rate(
        self,
        client: TestClient,
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """ARS->USD should divide by average rate."""
        # Insert a test rate
        rate = ExchangeRate(
            buy_rate=Decimal("1458.74"),
            sell_rate=Decimal("1459.32"),
            rate_date=Date(2026, 2, 1),
        )
        db.add(rate)
        db.commit()

        r = client.post(
            f"{settings.API_V1_STR}/currency/convert",
            headers=normal_user_token_headers,
            json={
                "amount": 145903,
                "from_currency": "ARS",
                "to_currency": "USD",
                "date": "2026-02-01",
            },
        )
        assert r.status_code == 200
        body = r.json()

        # Average rate: 1459.03
        # Rate for ARS->USD = 1 / 1459.03 ≈ 0.0006853
        # 145903 ARS * 0.0006853 ≈ 100 USD
        assert Decimal(str(body["converted_amount"])) == Decimal("100.00")
        assert body["rate_date"] == "2026-02-01"

    def test_convert_no_date_uses_latest_rate(
        self,
        client: TestClient,
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """No date provided should use latest rate."""
        # Insert multiple rates
        rate1 = ExchangeRate(
            buy_rate=Decimal("1458.74"),
            sell_rate=Decimal("1459.32"),
            rate_date=Date(2026, 2, 1),
        )
        rate2 = ExchangeRate(
            buy_rate=Decimal("1460.00"),
            sell_rate=Decimal("1461.00"),
            rate_date=Date(2026, 2, 5),
        )
        db.add(rate1)
        db.add(rate2)
        db.commit()

        r = client.post(
            f"{settings.API_V1_STR}/currency/convert",
            headers=normal_user_token_headers,
            json={"amount": 100, "from_currency": "USD", "to_currency": "ARS"},
        )
        assert r.status_code == 200
        body = r.json()

        # Should use latest rate (Feb 5)
        assert body["rate_date"] == "2026-02-05"

    def test_convert_falls_back_to_closest_date(
        self,
        client: TestClient,
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """Exact date not found falls back to closest date."""
        # Insert rates at Feb 1 and Feb 5
        rate1 = ExchangeRate(
            buy_rate=Decimal("1458.74"),
            sell_rate=Decimal("1459.32"),
            rate_date=Date(2026, 2, 1),
        )
        rate2 = ExchangeRate(
            buy_rate=Decimal("1460.00"),
            sell_rate=Decimal("1461.00"),
            rate_date=Date(2026, 2, 5),
        )
        db.add(rate1)
        db.add(rate2)
        db.commit()

        # Request rate for Feb 3 (closer to Feb 1)
        r = client.post(
            f"{settings.API_V1_STR}/currency/convert",
            headers=normal_user_token_headers,
            json={
                "amount": 100,
                "from_currency": "USD",
                "to_currency": "ARS",
                "date": "2026-02-03",
            },
        )
        assert r.status_code == 200
        body = r.json()

        # Should use Feb 1 (closest, prefers earlier when equidistant)
        assert body["rate_date"] == "2026-02-01"

    def test_convert_query_param_date_override(
        self,
        client: TestClient,
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """Query parameter date should override body date."""
        # Insert two rates
        rate1 = ExchangeRate(
            buy_rate=Decimal("1458.74"),
            sell_rate=Decimal("1459.32"),
            rate_date=Date(2026, 2, 1),
        )
        rate2 = ExchangeRate(
            buy_rate=Decimal("1460.00"),
            sell_rate=Decimal("1461.00"),
            rate_date=Date(2026, 2, 5),
        )
        db.add(rate1)
        db.add(rate2)
        db.commit()

        # Body date is Feb 1, but query param is Feb 5
        r = client.post(
            f"{settings.API_V1_STR}/currency/convert?date=2026-02-05",
            headers=normal_user_token_headers,
            json={
                "amount": 100,
                "from_currency": "USD",
                "to_currency": "ARS",
                "date": "2026-02-01",
            },
        )
        assert r.status_code == 200
        body = r.json()

        # Should use query param date (Feb 5)
        assert body["rate_date"] == "2026-02-05"

    def test_convert_no_rates_returns_404(
        self,
        client: TestClient,
        normal_user_token_headers: dict[str, str],
    ) -> None:
        """Empty database should return 404."""
        r = client.post(
            f"{settings.API_V1_STR}/currency/convert",
            headers=normal_user_token_headers,
            json={"amount": 100, "from_currency": "USD", "to_currency": "ARS"},
        )
        assert r.status_code == 404
        assert "No exchange rate" in r.json()["detail"]

    def test_convert_batch(
        self,
        client: TestClient,
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """Batch conversion should return results in order."""
        # Insert a rate
        rate = ExchangeRate(
            buy_rate=Decimal("1458.74"),
            sell_rate=Decimal("1459.32"),
            rate_date=Date(2026, 2, 1),
        )
        db.add(rate)
        db.commit()

        r = client.post(
            f"{settings.API_V1_STR}/currency/convert/batch",
            headers=normal_user_token_headers,
            json={
                "conversions": [
                    {"amount": 10, "from_currency": "USD", "to_currency": "ARS"},
                    {"amount": 14590.3, "from_currency": "ARS", "to_currency": "USD"},
                ]
            },
        )
        assert r.status_code == 200
        body = r.json()

        assert "results" in body
        assert len(body["results"]) == 2
        assert Decimal(str(body["results"][0]["converted_amount"])) == Decimal(
            "14590.30"
        )
        assert Decimal(str(body["results"][1]["converted_amount"])) == Decimal("10.00")
        assert body["results"][0]["rate_date"] == "2026-02-01"
        assert body["results"][1]["rate_date"] == "2026-02-01"

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

    def test_convert_invalid_date_format_returns_400(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        """Invalid date format should return a 400 error."""
        r = client.post(
            f"{settings.API_V1_STR}/currency/convert?date=invalid-date",
            headers=normal_user_token_headers,
            json={"amount": 100, "from_currency": "USD", "to_currency": "ARS"},
        )
        assert r.status_code == 400
        assert "Invalid date format" in r.json()["detail"]
