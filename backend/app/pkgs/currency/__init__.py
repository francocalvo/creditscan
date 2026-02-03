"""Currency package for multi-currency balance conversion.

Exports:
    ExchangeRateClient: HTTP client for exchange rate API
    CurrencyService: High-level currency conversion orchestration
    provide: Provider function for dependency injection
"""

from app.pkgs.currency.client import ExchangeRateClient
from app.pkgs.currency.service import CurrencyService, provide

__all__ = ["ExchangeRateClient", "CurrencyService", "provide"]
