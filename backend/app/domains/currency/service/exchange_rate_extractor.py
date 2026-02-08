"""Exchange rate extractor for Cronista Dólar MEP."""

import json
import logging
import re
from datetime import UTC, datetime
from datetime import date as Date
from decimal import Decimal

import httpx

from app.core.config import settings

from ..domain.errors import ExtractionError

logger = logging.getLogger(__name__)


class ExtractedRate:
    """Data class for extracted exchange rate."""

    def __init__(
        self,
        buy_rate: Decimal,
        sell_rate: Decimal,
        rate_date: Date,
        fetched_at: datetime,
        source: str = "cronista_mep",
    ) -> None:
        """Initialize extracted rate.

        Args:
            buy_rate: Buy (Compra) rate from source
            sell_rate: Sell (Venta) rate from source
            rate_date: Date for which the rate applies
            fetched_at: Timestamp when rate was fetched
            source: Source of the rate (default: cronista_mep)
        """
        self.buy_rate = buy_rate
        self.sell_rate = sell_rate
        self.rate_date = rate_date
        self.fetched_at = fetched_at
        self.source = source

    def __repr__(self) -> str:
        return (
            f"ExtractedRate(buy={self.buy_rate}, sell={self.sell_rate}, "
            f"date={self.rate_date}, source={self.source})"
        )


class ExchangeRateExtractor:
    """Service for extracting Dólar MEP rates from Cronista."""

    TIMEOUT = 30.0

    async def fetch_current_rate(self) -> ExtractedRate:
        """Fetch today's Dólar MEP rate from Cronista.

        Returns:
            ExtractedRate with buy_rate, sell_rate, rate_date, and fetched_at

        Raises:
            httpx.HTTPStatusError: If HTTP request fails
            httpx.TimeoutException: If request times out
            ExtractionError: If parsing fails
        """
        logger.info(f"Fetching current rate from {settings.CRONISTA_URL}")

        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            response = await client.get(settings.CRONISTA_URL)
            response.raise_for_status()

        logger.info("Successfully fetched Cronista page, parsing content")
        return self._parse_current_rate(response.text)

    def _parse_current_rate(self, html: str) -> ExtractedRate:
        """Extract rate data from Fusion.contentCache in HTML.

        Args:
            html: HTML content from Cronista page

        Returns:
            ExtractedRate with parsed data

        Raises:
            ExtractionError: If Fusion.contentCache is missing or invalid
        """
        # Find Fusion.contentCache in HTML
        # Pattern matches: Fusion.contentCache = {...}; followed by anything and Fusion.
        match = re.search(
            r"Fusion\.contentCache\s*=\s*(\{.*?\})\s*;.*?Fusion\.", html, re.DOTALL
        )
        if not match:
            raise ExtractionError(
                "Could not find Fusion.contentCache in Cronista page. "
                "Page structure may have changed."
            )

        # Parse JSON
        try:
            content_cache = json.loads(match.group(1))
        except json.JSONDecodeError as e:
            raise ExtractionError(f"Invalid JSON in contentCache: {e}")

        # Find markets-general data
        # The structure is: content_cache["markets-general"][<params_key>]["data"]
        # where <params_key> is a JSON-encoded parameter string.
        markets_data = None
        for key, value in content_cache.items():
            if "markets-general" in key.lower():
                if isinstance(value, dict):
                    # Check for data directly (legacy format)
                    data_list = value.get("data", [])
                    if data_list:
                        markets_data = data_list[0]
                        break
                    # Drill into nested param-keyed dicts
                    for inner in value.values():
                        if isinstance(inner, dict):
                            data_list = inner.get("data", [])
                            if data_list:
                                markets_data = data_list[0]
                                break
                    if markets_data:
                        break

        if not markets_data:
            raise ExtractionError(
                "Could not find 'markets-general' data in contentCache. "
                "Page structure may have changed."
            )

        # Extract required fields
        compra = markets_data.get("Compra")
        venta = markets_data.get("Venta")
        ultima_actualizacion = markets_data.get("UltimaActualizacion")

        if compra is None:
            raise ExtractionError(
                "Could not find 'Compra' (buy) rate in markets-general data"
            )

        if venta is None:
            raise ExtractionError(
                "Could not find 'Venta' (sell) rate in markets-general data"
            )

        if not ultima_actualizacion:
            raise ExtractionError(
                "Could not find 'UltimaActualizacion' timestamp in markets-general data"
            )

        # Parse .NET date format
        fetched_at = self._parse_dotnet_date(ultima_actualizacion)

        logger.info(f"Parsed rate: Compra={compra}, Venta={venta}, Date={fetched_at}")

        return ExtractedRate(
            buy_rate=Decimal(str(compra)),
            sell_rate=Decimal(str(venta)),
            rate_date=fetched_at.date(),
            fetched_at=fetched_at,
            source="cronista_mep",
        )

    def _parse_dotnet_date(self, date_str: str) -> datetime:
        """Parse .NET /Date(timestamp)/ format to UTC datetime.

        Args:
            date_str: Date string in format "/Date(1234567890000)/"

        Returns:
            UTC datetime object

        Raises:
            ExtractionError: If date format is invalid
        """
        match = re.search(r"/Date\((-?\d+)\)/", date_str)
        if not match:
            raise ExtractionError(
                f"Invalid .NET date format: '{date_str}'. "
                f"Expected format: /Date(timestamp)/"
            )

        try:
            ts_ms = int(match.group(1))
            return datetime.fromtimestamp(ts_ms / 1000, tz=UTC)
        except (ValueError, OSError) as e:
            raise ExtractionError(f"Could not parse timestamp '{date_str}': {e}")
