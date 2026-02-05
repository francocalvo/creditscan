"""Tests for currency rates query endpoint."""

from datetime import date as Date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.domains.currency.domain.models import ExchangeRate


class TestCurrencyRates:
    """Tests for GET /currency/rates."""

    def test_rates_requires_auth(self, client: TestClient) -> None:
        """Unauthenticated requests should be rejected."""
        r = client.get(f"{settings.API_V1_STR}/currency/rates")
        assert r.status_code == 401

    def test_rates_latest_default(
        self,
        client: TestClient,
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """Latest rate should be returned by default."""
        rate1 = ExchangeRate(
            buy_rate=Decimal("1000.00"),
            sell_rate=Decimal("1100.00"),
            rate_date=Date(2026, 2, 1),
        )
        rate2 = ExchangeRate(
            buy_rate=Decimal("1200.00"),
            sell_rate=Decimal("1300.00"),
            rate_date=Date(2026, 2, 5),
        )
        db.add(rate1)
        db.add(rate2)
        db.commit()

        r = client.get(
            f"{settings.API_V1_STR}/currency/rates",
            headers=normal_user_token_headers,
        )
        assert r.status_code == 200
        body = r.json()

        assert body["base_currency"] == "USD"
        assert body["target_currency"] == "ARS"
        assert len(body["rates"]) == 1
        assert body["rates"][0]["rate_date"] == "2026-02-05"
        assert Decimal(str(body["rates"][0]["buy_rate"])) == Decimal("1200.00")
        assert Decimal(str(body["rates"][0]["sell_rate"])) == Decimal("1300.00")
        assert Decimal(str(body["rates"][0]["average_rate"])) == Decimal("1250.00")

    def test_rates_exact_date(
        self,
        client: TestClient,
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """Specific date query should return that date's rate."""
        rate1 = ExchangeRate(
            buy_rate=Decimal("1000.00"),
            sell_rate=Decimal("1100.00"),
            rate_date=Date(2026, 2, 1),
        )
        db.add(rate1)
        db.commit()

        r = client.get(
            f"{settings.API_V1_STR}/currency/rates?date=2026-02-01",
            headers=normal_user_token_headers,
        )
        assert r.status_code == 200
        body = r.json()

        assert len(body["rates"]) == 1
        assert body["rates"][0]["rate_date"] == "2026-02-01"

    def test_rates_closest_fallback(
        self,
        client: TestClient,
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """Specific date query should fall back to closest date if exact match not found."""
        rate1 = ExchangeRate(
            buy_rate=Decimal("1000.00"),
            sell_rate=Decimal("1100.00"),
            rate_date=Date(2026, 2, 1),
        )
        rate2 = ExchangeRate(
            buy_rate=Decimal("1200.00"),
            sell_rate=Decimal("1300.00"),
            rate_date=Date(2026, 2, 5),
        )
        db.add(rate1)
        db.add(rate2)
        db.commit()

        # Request Feb 3, should get Feb 1
        r = client.get(
            f"{settings.API_V1_STR}/currency/rates?date=2026-02-03",
            headers=normal_user_token_headers,
        )
        assert r.status_code == 200
        body = r.json()

        assert len(body["rates"]) == 1
        assert body["rates"][0]["rate_date"] == "2026-02-01"

    def test_rates_date_range(
        self,
        client: TestClient,
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """Range query should return all rates in interval, sorted by date."""
        rates = [
            ExchangeRate(
                buy_rate=Decimal("1000") + i,
                sell_rate=Decimal("1100") + i,
                rate_date=Date(2026, 2, i),
            )
            for i in range(1, 6)
        ]
        for r in rates:
            db.add(r)
        db.commit()

        r = client.get(
            f"{settings.API_V1_STR}/currency/rates?start_date=2026-02-02&end_date=2026-02-04",
            headers=normal_user_token_headers,
        )
        assert r.status_code == 200
        body = r.json()

        assert len(body["rates"]) == 3
        assert body["rates"][0]["rate_date"] == "2026-02-02"
        assert body["rates"][1]["rate_date"] == "2026-02-03"
        assert body["rates"][2]["rate_date"] == "2026-02-04"

    def test_rates_empty_db_returns_200(
        self,
        client: TestClient,
        normal_user_token_headers: dict[str, str],
    ) -> None:
        """Empty database should return 200 with empty list."""
        r = client.get(
            f"{settings.API_V1_STR}/currency/rates",
            headers=normal_user_token_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["rates"] == []

    def test_rates_ars_to_usd_inversion(
        self,
        client: TestClient,
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """ARS->USD should return inverted rates."""
        rate = ExchangeRate(
            buy_rate=Decimal("1000.0000"),
            sell_rate=Decimal("1100.0000"),
            rate_date=Date(2026, 2, 1),
        )
        db.add(rate)
        db.commit()

        r = client.get(
            f"{settings.API_V1_STR}/currency/rates?base=ARS&target=USD",
            headers=normal_user_token_headers,
        )
        assert r.status_code == 200
        body = r.json()

        assert body["base_currency"] == "ARS"
        assert body["target_currency"] == "USD"
        assert len(body["rates"]) == 1

        # Inverted Buy = 1 / 1100 = 0.00090909... -> 0.0009
        # Inverted Sell = 1 / 1000 = 0.001
        # Average = (0.00090909 + 0.001) / 2 = 0.0009545... -> 0.001
        # With 4 decimal precision:
        # 1/1100 = 0.0009
        # 1/1000 = 0.0010
        # Avg = 0.00095 -> 0.0010 (quantized)

        rate_resp = body["rates"][0]
        assert Decimal(str(rate_resp["buy_rate"])) == (
            Decimal("1") / Decimal("1100")
        ).quantize(Decimal("0.0001"))
        assert Decimal(str(rate_resp["sell_rate"])) == (
            Decimal("1") / Decimal("1000")
        ).quantize(Decimal("0.0001"))
        assert Decimal(str(rate_resp["average_rate"])) == (
            (Decimal("1") / Decimal("1100") + Decimal("1") / Decimal("1000")) / 2
        ).quantize(Decimal("0.0001"))

    def test_rates_validation_errors(
        self,
        client: TestClient,
        normal_user_token_headers: dict[str, str],
    ) -> None:
        """Check various validation errors."""
        # base == target
        r = client.get(
            f"{settings.API_V1_STR}/currency/rates?base=USD&target=USD",
            headers=normal_user_token_headers,
        )
        assert r.status_code == 400
        assert "same" in r.json()["detail"]

        # Unsupported currency
        r = client.get(
            f"{settings.API_V1_STR}/currency/rates?base=EUR",
            headers=normal_user_token_headers,
        )
        assert r.status_code == 400
        assert "Unsupported" in r.json()["detail"]

        # Conflict date params
        r = client.get(
            f"{settings.API_V1_STR}/currency/rates?date=2026-02-01&start_date=2026-02-01",
            headers=normal_user_token_headers,
        )
        assert r.status_code == 400
        assert "Cannot combine" in r.json()["detail"]

        # Missing range param
        r = client.get(
            f"{settings.API_V1_STR}/currency/rates?start_date=2026-02-01",
            headers=normal_user_token_headers,
        )
        assert r.status_code == 400
        assert "Both" in r.json()["detail"]

        # Invalid range order
        r = client.get(
            f"{settings.API_V1_STR}/currency/rates?start_date=2026-02-05&end_date=2026-02-01",
            headers=normal_user_token_headers,
        )
        assert r.status_code == 400
        assert "less than" in r.json()["detail"]
