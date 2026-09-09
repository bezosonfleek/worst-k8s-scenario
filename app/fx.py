import json
import requests

from app.config import BASE_CURRENCY, FX_RATE_CACHE_TTL_SECONDS
from app.redis_client import r

FX_CACHE_KEY = f"fx:rates:{BASE_CURRENCY}"

# Free, no-API-key-required FX rate provider. If this ever becomes
# unreliable/rate-limited, swap the URL here — nothing else needs to change,
# since callers only ever see get_rate()'s return value.
FX_API_URL = f"https://api.exchangerate-api.com/v4/latest/{BASE_CURRENCY}"


def _fetch_rates_from_api() -> dict:
    resp = requests.get(FX_API_URL, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    return data["rates"]  # e.g. {"USD": 0.0077, "EUR": 0.0071, ...}


def get_rates() -> dict:
    """
    Returns a dict of {currency_code: rate_from_base}, cached in Redis for
    FX_RATE_CACHE_TTL_SECONDS so we don't hit the external API on every
    single request — bidding logic never touches this, it's purely for
    displaying an already-stored KES amount in another currency.
    """
    cached = r.get(FX_CACHE_KEY)
    if cached:
        return json.loads(cached)

    rates = _fetch_rates_from_api()
    r.setex(FX_CACHE_KEY, FX_RATE_CACHE_TTL_SECONDS, json.dumps(rates))
    return rates


def convert(amount_base: float, target_currency: str) -> float:
    target_currency = target_currency.upper()
    if target_currency == BASE_CURRENCY:
        return round(amount_base, 2)

    rates = get_rates()
    if target_currency not in rates:
        raise ValueError(f"Unsupported currency: {target_currency}")

    return round(amount_base * rates[target_currency], 2)
