from fastapi import APIRouter, HTTPException, Query

from app.config import BASE_CURRENCY
from app.fx import get_rates, convert

router = APIRouter(prefix="/fx", tags=["currency"])


@router.get("/rates")
def rates():
    """All bids are stored/compared in KES internally — this is display-only."""
    try:
        return {"base": BASE_CURRENCY, "rates": get_rates()}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Could not fetch FX rates: {e}")


@router.get("/convert")
def convert_amount(
    amount_kes: float = Query(..., gt=0),
    to: str = Query(..., min_length=3, max_length=3),
):
    try:
        converted = convert(amount_kes, to)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Could not fetch FX rates: {e}")

    return {"amount_kes": amount_kes, "currency": to.upper(), "converted_amount": converted}
