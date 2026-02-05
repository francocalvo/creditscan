"""Tests for exchange rate extractor service."""

from datetime import UTC, datetime
from datetime import date as Date
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.core.config import settings
from app.domains.currency.service.exchange_rate_extractor import (
    ExchangeRateExtractor,
    ExtractedRate,
    ExtractionError,
)

# HTML Fixtures for testing
VALID_HTML_FIXTURE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cronista Dólar MEP</title>
    <script>
        Fusion.contentCache = {
            "markets-general": {
                "data": [{
                    "Compra": 1020.50,
                    "Venta": 1045.75,
                    "UltimaActualizacion": "/Date(1737676800000)/"
                }]
            }
        };
    Fusion.init();
    </script>
</head>
<body>
    <div class="markets-general"></div>
</body>
</html>
"""

MISSING_CACHE_HTML_FIXTURE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cronista Dólar MEP</title>
    <script>
        Fusion.init();
    </script>
</head>
<body></body>
</html>
"""

INVALID_JSON_HTML_FIXTURE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cronista Dólar MEP</title>
    <script>
        Fusion.contentCache = {invalid json};
        Fusion.init();
    </script>
</head>
<body></body>
</html>
"""

MISSING_MARKETS_DATA_HTML_FIXTURE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cronista Dólar MEP</title>
    <script>
        Fusion.contentCache = {
            "other-key": {
                "data": []
            }
        };
        Fusion.init();
    </script>
</head>
<body></body>
</html>
"""

MISSING_COMPRA_HTML_FIXTURE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cronista Dólar MEP</title>
    <script>
        Fusion.contentCache = {
            "markets-general": {
                "data": [{
                    "Venta": 1045.75,
                    "UltimaActualizacion": "/Date(1737676800000)/"
                }]
            }
        };
        Fusion.init();
    </script>
</head>
<body></body>
</html>
"""

MISSING_VENTA_HTML_FIXTURE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cronista Dólar MEP</title>
    <script>
        Fusion.contentCache = {
            "markets-general": {
                "data": [{
                    "Compra": 1020.50,
                    "UltimaActualizacion": "/Date(1737676800000)/"
                }]
            }
        };
        Fusion.init();
    </script>
</head>
<body></body>
</html>
"""

MISSING_TIMESTAMP_HTML_FIXTURE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cronista Dólar MEP</title>
    <script>
        Fusion.contentCache = {
            "markets-general": {
                "data": [{
                    "Compra": 1020.50,
                    "Venta": 1045.75
                }]
            }
        };
        Fusion.init();
    </script>
</head>
<body></body>
</html>
"""

INVALID_DATE_FORMAT_HTML_FIXTURE = """
<!DOCTYPE html>
<html>
<head>
    <title>Cronista Dólar MEP</title>
    <script>
        Fusion.contentCache = {
            "markets-general": {
                "data": [{
                    "Compra": 1020.50,
                    "Venta": 1045.75,
                    "UltimaActualizacion": "invalid-date"
                }]
            }
        };
        Fusion.init();
    </script>
</head>
<body></body>
</html>
"""


class TestExtractedRate:
    """Test ExtractedRate data class."""

    def test_extracted_rate_initialization(self) -> None:
        """Test that ExtractedRate can be initialized correctly."""
        rate = ExtractedRate(
            buy_rate=Decimal("1020.50"),
            sell_rate=Decimal("1045.75"),
            rate_date=Date(2025, 1, 24),
            fetched_at=datetime(2025, 1, 24, 12, 0, 0, tzinfo=UTC),
            source="cronista_mep",
        )

        assert rate.buy_rate == Decimal("1020.50")
        assert rate.sell_rate == Decimal("1045.75")
        assert rate.rate_date == Date(2025, 1, 24)
        assert rate.fetched_at == datetime(2025, 1, 24, 12, 0, 0, tzinfo=UTC)
        assert rate.source == "cronista_mep"

    def test_extracted_rate_default_source(self) -> None:
        """Test that default source is cronista_mep."""
        rate = ExtractedRate(
            buy_rate=Decimal("1020.50"),
            sell_rate=Decimal("1045.75"),
            rate_date=Date(2025, 1, 24),
            fetched_at=datetime(2025, 1, 24, 12, 0, 0, tzinfo=UTC),
        )

        assert rate.source == "cronista_mep"

    def test_extracted_rate_repr(self) -> None:
        """Test ExtractedRate string representation."""
        rate = ExtractedRate(
            buy_rate=Decimal("1020.50"),
            sell_rate=Decimal("1045.75"),
            rate_date=Date(2025, 1, 24),
            fetched_at=datetime(2025, 1, 24, 12, 0, 0, tzinfo=UTC),
        )

        repr_str = repr(rate)
        assert "buy=1020.50" in repr_str
        assert "sell=1045.75" in repr_str
        assert "date=2025-01-24" in repr_str
        assert "source=cronista_mep" in repr_str


class TestExchangeRateExtractor:
    """Test ExchangeRateExtractor service."""

    def test_parse_current_rate_valid_html(self) -> None:
        """Test parsing valid HTML with Fusion.contentCache."""
        extractor = ExchangeRateExtractor()
        rate = extractor._parse_current_rate(VALID_HTML_FIXTURE)

        assert isinstance(rate, ExtractedRate)
        assert rate.buy_rate == Decimal("1020.50")
        assert rate.sell_rate == Decimal("1045.75")
        assert rate.rate_date == Date(2025, 1, 24)
        # 1737676800000 ms = January 24, 2025 00:00:00 UTC
        assert rate.fetched_at == datetime(2025, 1, 24, 0, 0, 0, tzinfo=UTC)
        assert rate.source == "cronista_mep"

    def test_parse_current_rate_missing_cache_raises(self) -> None:
        """Test that missing Fusion.contentCache raises ExtractionError."""
        extractor = ExchangeRateExtractor()
        with pytest.raises(ExtractionError) as exc_info:
            extractor._parse_current_rate(MISSING_CACHE_HTML_FIXTURE)

        assert "Could not find Fusion.contentCache" in str(exc_info.value)

    def test_parse_current_rate_invalid_json_raises(self) -> None:
        """Test that invalid JSON in contentCache raises ExtractionError."""
        extractor = ExchangeRateExtractor()
        with pytest.raises(ExtractionError) as exc_info:
            extractor._parse_current_rate(INVALID_JSON_HTML_FIXTURE)

        assert "Invalid JSON in contentCache" in str(exc_info.value)

    def test_parse_current_rate_missing_markets_data_raises(self) -> None:
        """Test that missing markets-general data raises ExtractionError."""
        extractor = ExchangeRateExtractor()
        with pytest.raises(ExtractionError) as exc_info:
            extractor._parse_current_rate(MISSING_MARKETS_DATA_HTML_FIXTURE)

        assert "Could not find 'markets-general' data" in str(exc_info.value)

    def test_parse_current_rate_missing_compra_raises(self) -> None:
        """Test that missing Compra field raises ExtractionError."""
        extractor = ExchangeRateExtractor()
        with pytest.raises(ExtractionError) as exc_info:
            extractor._parse_current_rate(MISSING_COMPRA_HTML_FIXTURE)

        assert "Could not find 'Compra' (buy) rate" in str(exc_info.value)

    def test_parse_current_rate_missing_venta_raises(self) -> None:
        """Test that missing Venta field raises ExtractionError."""
        extractor = ExchangeRateExtractor()
        with pytest.raises(ExtractionError) as exc_info:
            extractor._parse_current_rate(MISSING_VENTA_HTML_FIXTURE)

        assert "Could not find 'Venta' (sell) rate" in str(exc_info.value)

    def test_parse_current_rate_missing_timestamp_raises(self) -> None:
        """Test that missing UltimaActualizacion raises ExtractionError."""
        extractor = ExchangeRateExtractor()
        with pytest.raises(ExtractionError) as exc_info:
            extractor._parse_current_rate(MISSING_TIMESTAMP_HTML_FIXTURE)

        assert "Could not find 'UltimaActualizacion' timestamp" in str(exc_info.value)

    def test_parse_current_rate_invalid_date_format_raises(self) -> None:
        """Test that invalid date format raises ExtractionError."""
        extractor = ExchangeRateExtractor()
        with pytest.raises(ExtractionError) as exc_info:
            extractor._parse_current_rate(INVALID_DATE_FORMAT_HTML_FIXTURE)

        assert "Invalid .NET date format" in str(exc_info.value)

    def test_parse_dotnet_date_valid_format(self) -> None:
        """Test parsing valid .NET date format."""
        extractor = ExchangeRateExtractor()
        # January 24, 2025 00:00:00 UTC (1737676800000 ms)
        result = extractor._parse_dotnet_date("/Date(1737676800000)/")

        assert result == datetime(2025, 1, 24, 0, 0, 0, tzinfo=UTC)

    def test_parse_dotnet_date_zero_timestamp(self) -> None:
        """Test parsing epoch timestamp."""
        extractor = ExchangeRateExtractor()
        result = extractor._parse_dotnet_date("/Date(0)/")

        assert result == datetime(1970, 1, 1, 0, 0, 0, tzinfo=UTC)

    def test_parse_dotnet_date_invalid_format_raises(self) -> None:
        """Test that invalid date format raises ExtractionError."""
        extractor = ExchangeRateExtractor()
        with pytest.raises(ExtractionError) as exc_info:
            extractor._parse_dotnet_date("invalid-date")

        assert "Invalid .NET date format" in str(exc_info.value)

    def test_parse_dotnet_date_invalid_timestamp_raises(self) -> None:
        """Test that invalid timestamp format raises ExtractionError."""
        extractor = ExchangeRateExtractor()
        with pytest.raises(ExtractionError) as exc_info:
            extractor._parse_dotnet_date("/Date(not-a-number)/")

        # /Date(not-a-number)/ doesn't match the expected /Date(digits)/ pattern
        assert "Invalid .NET date format" in str(exc_info.value)

    def test_parse_dotnet_date_negative_timestamp(self) -> None:
        """Test parsing negative timestamp (before epoch)."""
        extractor = ExchangeRateExtractor()
        # One day before epoch in milliseconds
        result = extractor._parse_dotnet_date("/Date(-86400000)/")

        assert result == datetime(1969, 12, 31, 0, 0, 0, tzinfo=UTC)

    @pytest.mark.asyncio
    async def test_fetch_current_rate_success(self) -> None:
        """Test successful fetching and parsing of current rate."""
        extractor = ExchangeRateExtractor()

        # Mock httpx.AsyncClient
        mock_response = Mock()
        mock_response.text = VALID_HTML_FIXTURE
        mock_response.raise_for_status = Mock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch(
            "app.domains.currency.service.exchange_rate_extractor.httpx.AsyncClient",
            return_value=mock_client,
        ):
            rate = await extractor.fetch_current_rate()

        assert rate.buy_rate == Decimal("1020.50")
        assert rate.sell_rate == Decimal("1045.75")
        assert rate.rate_date == Date(2025, 1, 24)
        mock_client.get.assert_called_once_with(settings.CRONISTA_URL)
        mock_response.raise_for_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_current_rate_http_error_propagates(self) -> None:
        """Test that HTTP errors are propagated (not wrapped)."""
        import httpx

        extractor = ExchangeRateExtractor()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Server error", request=Mock(), response=Mock()
            )
        )

        with patch(
            "app.domains.currency.service.exchange_rate_extractor.httpx.AsyncClient",
            return_value=mock_client,
        ):
            with pytest.raises(httpx.HTTPStatusError):
                await extractor.fetch_current_rate()

    @pytest.mark.asyncio
    async def test_fetch_current_rate_timeout_propagates(self) -> None:
        """Test that timeout errors are propagated."""
        import httpx

        extractor = ExchangeRateExtractor()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

        with patch(
            "app.domains.currency.service.exchange_rate_extractor.httpx.AsyncClient",
            return_value=mock_client,
        ):
            with pytest.raises(httpx.TimeoutException):
                await extractor.fetch_current_rate()

    def test_timeout_constant(self) -> None:
        """Test that TIMEOUT constant is set correctly."""
        assert ExchangeRateExtractor.TIMEOUT == 30.0
