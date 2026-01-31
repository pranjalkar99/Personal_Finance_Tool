"""Currency conversion service."""

from decimal import Decimal
from typing import Dict
from datetime import datetime


# Static exchange rates (relative to INR)
# In production, these would come from an external API
EXCHANGE_RATES: Dict[str, Decimal] = {
    "INR": Decimal("1.0"),
    "USD": Decimal("83.50"),      # 1 USD = 83.50 INR
    "EUR": Decimal("90.25"),      # 1 EUR = 90.25 INR
    "GBP": Decimal("105.75"),     # 1 GBP = 105.75 INR
    "JPY": Decimal("0.56"),       # 1 JPY = 0.56 INR
    "AUD": Decimal("54.50"),      # 1 AUD = 54.50 INR
    "CAD": Decimal("61.25"),      # 1 CAD = 61.25 INR
}


class CurrencyService:
    """Service for currency operations."""

    @staticmethod
    def get_supported_currencies() -> list[str]:
        """Get list of supported currency codes."""
        return list(EXCHANGE_RATES.keys())

    @staticmethod
    def get_rate(from_currency: str, to_currency: str = "INR") -> Decimal:
        """Get exchange rate between two currencies."""
        from_rate = EXCHANGE_RATES.get(from_currency.upper(), Decimal("1.0"))
        to_rate = EXCHANGE_RATES.get(to_currency.upper(), Decimal("1.0"))
        
        # Convert: amount_in_from * from_rate / to_rate = amount_in_to
        if to_rate == 0:
            return Decimal("1.0")
        return from_rate / to_rate

    @staticmethod
    def convert(amount: Decimal, from_currency: str, to_currency: str = "INR") -> Decimal:
        """Convert amount from one currency to another."""
        rate = CurrencyService.get_rate(from_currency, to_currency)
        return round(amount * rate, 2)

    @staticmethod
    def get_all_rates(base_currency: str = "INR") -> Dict[str, Decimal]:
        """Get all exchange rates relative to a base currency."""
        base_rate = EXCHANGE_RATES.get(base_currency.upper(), Decimal("1.0"))
        return {
            code: round(rate / base_rate, 4) if base_rate > 0 else rate
            for code, rate in EXCHANGE_RATES.items()
        }

    @staticmethod
    def format_currency(amount: Decimal, currency: str) -> str:
        """Format amount with currency symbol."""
        symbols = {
            "INR": "₹",
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
            "JPY": "¥",
            "AUD": "A$",
            "CAD": "C$"
        }
        symbol = symbols.get(currency.upper(), currency)
        return f"{symbol}{amount:,.2f}"

