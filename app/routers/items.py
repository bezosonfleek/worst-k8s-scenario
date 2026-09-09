from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, schemas, models
from app.database import get_db
from app.redis_client import seed_highest_bid, get_highest_bid

router = APIRouter(prefix="/items", tags=["items"])


def _require_admin(db: Session, acting_user_id: str) -> models.User:
    """
    No real auth yet (see design notes — deferred to a later phase).
    For now, the caller just tells us who they are via acting_user_id, and we
    check that user's is_admin flag. Good enough to prove the approval flow;
    replace with real auth (JWT/session) before this is ever public-facing.
    """
    user = crud.get_user(db, acting_user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Acting user not found")
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user


@router.post("", response_model=schemas.ItemOut, status_code=201)
def create_item(item_in: schemas.ItemCreate, db: Session = Depends(get_db)):
    seller = crud.get_user(db, item_in.seller_id)
    if seller is None:
        raise HTTPException(status_code=404, detail="Seller (user) not found")
    if item_in.ends_at <= item_in.starts_at:
        raise HTTPException(status_code=422, detail="ends_at must be after starts_at")
    return crud.create_item(db, item_in)


@router.get("", response_model=list[schemas.ItemOut])
def list_items(
    status: models.ItemStatus | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return crud.list_items(db, status=status)


@router.get("/{item_id}", response_model=schemas.ItemDetailOut)
def get_item(item_id: str, db: Session = Depends(get_db)):
    item = crud.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    bids = crud.list_bids_for_item(db, item_id)
    # Prefer Redis's view of the highest bid (fast, always current); fall back to DB.
    highest = get_highest_bid(item_id)
    highest_kes = highest if highest is not None else (
        str(bids[0].amount_kes) if bids else None
    )

    out = schemas.ItemDetailOut.model_validate(item)
    out.bids = [schemas.BidOut.model_validate(b) for b in bids]
    out.highest_bid_kes = highest_kes
    return out


@router.patch("/{item_id}/status", response_model=schemas.ItemOut)
def update_status(
    item_id: str,
    status_update: schemas.ItemStatusUpdate,
    acting_user_id: str = Query(..., description="user_id of the admin performing this action"),
    db: Session = Depends(get_db),
):
    _require_admin(db, acting_user_id)

    item = crud.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.status != models.ItemStatus.pending:
        raise HTTPException(status_code=409, detail=f"Item is already '{item.status.value}', not pending")

    if status_update.status not in (models.ItemStatus.approved, models.ItemStatus.rejected):
        raise HTTPException(status_code=422, detail="status must be 'approved' or 'rejected'")

    updated = crud.update_item_status(db, item, status_update.status)

    # Seed Redis with the starting price the moment an item is approved, so the
    # atomic bid-check has a baseline to compare against as soon as bidding opens.
    if updated.status == models.ItemStatus.approved:
        seed_highest_bid(item_id, str(updated.starting_price_kes))

    return updated
