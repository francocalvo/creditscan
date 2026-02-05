from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.domains.currency.domain.models import ExchangeRate

# Fixtures


@pytest.fixture
def mock_cronista_response():
    """Returns a mock HTML response from Cronista."""
    # Using a fixed timestamp for 2026-02-04 12:00:00 UTC = 1770206400000 ms
    timestamp_ms = 1770206400000
    html_content = f"""
    <html>
        <script>
            Fusion.contentCache = {{
                "some-markets-general-key": {{
                    "data": [
                        {{
                            "Compra": 1200.50,
                            "Venta": 1205.50,
                            "UltimaActualizacion": "/Date({timestamp_ms})/"
                        }}
                    ]
                }}
            }};
            Fusion.someOtherProperty = "ignored";
        </script>
    </html>
    """
    mock_resp = Mock()
    mock_resp.text = html_content
    mock_resp.raise_for_status = Mock()
    return mock_resp


@pytest.fixture
def mock_httpx_client(mock_cronista_response):
    """Mocks httpx.AsyncClient to return the controlled response."""
    with patch(
        "app.domains.currency.service.exchange_rate_extractor.httpx.AsyncClient"
    ) as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get.return_value = mock_cronista_response
        mock_client_cls.return_value = mock_client
        yield mock_client


@pytest.fixture
def patch_extraction_session(db: Session):
    """
    Patches get_db_session in the extract route to share the test DB connection.
    This ensures background tasks write to the same transaction-managed DB as the test.
    """

    # Create a new session bound to the same connection/transaction as the test session
    # We use a factory function to return a new session for each call,
    # but bound to the existing test connection.
    def get_test_session():
        return Session(bind=db.connection())

    with patch(
        "app.api.routes.currency.extract.get_db_session", side_effect=get_test_session
    ):
        yield


def seed_rate(db: Session, rate_date: date, buy: Decimal, sell: Decimal):
    rate = ExchangeRate(
        buy_rate=buy,
        sell_rate=sell,
        rate_date=rate_date,
        source="seed",
        fetched_at=datetime.now(UTC),
    )
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate


class TestCurrencyIntegration:
    def test_convert_with_seeded_rate_success(
        self, client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
    ):
        """Test simple conversion using a pre-seeded rate."""
        target_date = date(2026, 2, 4)
        seed_rate(db, target_date, Decimal("1000.00"), Decimal("1020.00"))

        # Average rate = 1010.00
        # 100 USD -> 101,000 ARS

        payload = {
            "amount": 100,
            "from_currency": "USD",
            "to_currency": "ARS",
            "date": target_date.isoformat(),
        }

        response = client.post(
            f"{settings.API_V1_STR}/currency/convert",
            headers=normal_user_token_headers,
            json=payload,
        )

        assert response.status_code == 200
        data = response.json()
        assert float(data["converted_amount"]) == 101000.0
        assert float(data["rate"]) == 1010.0
        assert data["rate_date"] == target_date.isoformat()

    def test_extract_then_convert_e2e_success(
        self,
        client: TestClient,
        db: Session,
        superuser_token_headers: dict[str, str],
        normal_user_token_headers: dict[str, str],
        mock_httpx_client,
        patch_extraction_session,
    ):
        """
        True E2E test:
        1. Start with empty DB (for this date).
        2. Admin triggers extraction (mocked HTTP, real DB write).
        3. Background task runs and commits to DB.
        4. User requests conversion (reading from DB).
        """
        # Ensure no rates exist for our mock date (2026-02-04)
        # (Implicitly true if DB is clean per test)

        # 1. Trigger extraction as Admin
        extract_response = client.post(
            f"{settings.API_V1_STR}/currency/rates/extract",
            headers=superuser_token_headers,
        )
        assert extract_response.status_code == 202

        # NOTE: TestClient runs background tasks synchronously before returning response
        # So by here, the rate should be in the DB.

        # 2. Verify Rate is in DB (optional, but good for debugging)
        # Expected from mock: Buy=1200.50, Sell=1205.50 -> Avg=1203.00
        # Date from mock timestamp 1770206400000 -> 2026-02-04

        # 3. User converts USD to ARS
        payload = {
            "amount": 10,
            "from_currency": "USD",
            "to_currency": "ARS",
            # No date provided -> use latest (which we just extracted)
        }

        convert_response = client.post(
            f"{settings.API_V1_STR}/currency/convert",
            headers=normal_user_token_headers,
            json=payload,
        )

        assert convert_response.status_code == 200
        data = convert_response.json()
        assert float(data["rate"]) == 1203.0
        assert float(data["converted_amount"]) == 12030.0
        assert data["rate_date"] == "2026-02-04"

    def test_convert_no_rates_404(
        self, client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
    ):
        """Test conversion fails with 404 if no rates exist."""
        payload = {"amount": 100, "from_currency": "USD", "to_currency": "ARS"}
        response = client.post(
            f"{settings.API_V1_STR}/currency/convert",
            headers=normal_user_token_headers,
            json=payload,
        )
        assert response.status_code == 404
        assert "No exchange rate available" in response.json()["detail"]

    def test_convert_invalid_currency_400(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ):
        """Test conversion fails with 400 for unsupported currency."""
        payload = {"amount": 100, "from_currency": "USD", "to_currency": "EUR"}
        response = client.post(
            f"{settings.API_V1_STR}/currency/convert",
            headers=normal_user_token_headers,
            json=payload,
        )
        assert response.status_code == 400
        assert "Unsupported currency: EUR" in response.json()["detail"]

    def test_convert_historical_date_success(
        self, client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
    ):
        """Test conversion with a specific past date."""
        # Seed two dates
        seed_rate(db, date(2026, 1, 1), Decimal("100.00"), Decimal("100.00"))  # Avg 100
        seed_rate(db, date(2026, 2, 1), Decimal("200.00"), Decimal("200.00"))  # Avg 200

        payload = {
            "amount": 50,
            "from_currency": "USD",
            "to_currency": "ARS",
            "date": "2026-01-01",
        }

        response = client.post(
            f"{settings.API_V1_STR}/currency/convert",
            headers=normal_user_token_headers,
            json=payload,
        )

        assert response.status_code == 200
        data = response.json()
        assert float(data["rate"]) == 100.0
        assert float(data["converted_amount"]) == 5000.0
        assert data["rate_date"] == "2026-01-01"

    def test_rates_query_success(
        self, client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
    ):
        """Test querying rates with a date range."""
        seed_rate(db, date(2026, 2, 1), Decimal("1000.00"), Decimal("1010.00"))
        seed_rate(db, date(2026, 2, 2), Decimal("1020.00"), Decimal("1030.00"))
        seed_rate(db, date(2026, 2, 3), Decimal("1040.00"), Decimal("1050.00"))

        response = client.get(
            f"{settings.API_V1_STR}/currency/rates?start_date=2026-02-01&end_date=2026-02-02",
            headers=normal_user_token_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["rates"]) == 2
        assert data["rates"][0]["rate_date"] == "2026-02-01"
        assert data["rates"][1]["rate_date"] == "2026-02-02"
        assert float(data["rates"][0]["average_rate"]) == 1005.0
