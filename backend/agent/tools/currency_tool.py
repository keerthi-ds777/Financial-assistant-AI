import requests
from langchain_core.tools import tool
from backend.config import settings

CURRENCY_API_BASE = "https://api.exchangerate-api.com/v4/latest"

@tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """
    Convert an amount from one currency to another.
    Use this when the user asks about currency conversion, exchange rates, or
    wants to know the equivalent value in another currency.
    Examples: USD to INR, EUR to GBP, 100 USD to JPY
    """
    try:
        from_currency = from_currency.upper().strip()
        to_currency = to_currency.upper().strip()

        # Try free ExchangeRate-API first
        response = requests.get(f"{CURRENCY_API_BASE}/{from_currency}", timeout=10)

        if response.status_code == 200:
            data = response.json()
            rates = data.get("rates", {})

            if to_currency not in rates:
                return f"Currency '{to_currency}' not found. Please use a valid ISO 4217 currency code."

            rate = rates[to_currency]
            converted = round(amount * rate, 4)

            return (
                f"**Currency Conversion**\n"
                f"- {amount:,.2f} {from_currency} = **{converted:,.4f} {to_currency}**\n"
                f"- Exchange Rate: 1 {from_currency} = {rate} {to_currency}"
            )

        # Fallback: CurrencyConverter API
        api_key = settings.CURRENCY_API_KEY
        fallback_url = (
            f"https://api.currencyconverterapi.com/api/v7/convert"
            f"?q={from_currency}_{to_currency}&compact=ultra&apiKey={api_key}"
        )
        fb_response = requests.get(fallback_url, timeout=10)
        if fb_response.status_code == 200:
            fb_data = fb_response.json()
            rate = fb_data.get(f"{from_currency}_{to_currency}", None)
            if rate:
                converted = round(amount * rate, 4)
                return (
                    f"**Currency Conversion**\n"
                    f"- {amount:,.2f} {from_currency} = **{converted:,.4f} {to_currency}**\n"
                    f"- Exchange Rate: 1 {from_currency} = {rate} {to_currency}"
                )

        return "Unable to fetch exchange rates at this time. Please try again later."

    except Exception as e:
        return f"Currency conversion error: {str(e)}"


@tool
def get_exchange_rate(from_currency: str, to_currency: str) -> str:
    """
    Get the current exchange rate between two currencies.
    Use when the user asks 'what is the exchange rate' without specifying an amount.
    """
    try:
        from_currency = from_currency.upper().strip()
        to_currency = to_currency.upper().strip()

        response = requests.get(f"{CURRENCY_API_BASE}/{from_currency}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            rates = data.get("rates", {})
            if to_currency in rates:
                rate = rates[to_currency]
                return f"1 {from_currency} = {rate} {to_currency}"

        return f"Could not fetch rate for {from_currency} → {to_currency}."
    except Exception as e:
        return f"Error: {str(e)}"
