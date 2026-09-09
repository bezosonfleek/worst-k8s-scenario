from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas, models
from app.config import ANTI_SNIPE_WINDOW_SECONDS, ANTI_SNIPE_EXTENSION_SECONDS
from app.database import get_db
from app.redis_client import try_place_bid, publish_event, set_ends_at

router = APIRouter(prefix="/items/{item_id}/bids", tags=["bids"])


@router.post("", response_model=schemas.BidOut, status_code=201)
def place_bid(item_id: str, bid_in: schemas.BidCreate, db: Session = Depends(get_db)):
    item = crud.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    bidder = crud.get_user(db, bid_in.bidder_id)
    if bidder is None:
        raise HTTPException(status_code=404, detail="Bidder (user) not found")

    now = datetime.utcnow()
    if not crud.is_item_live(item, now):
        raise HTTPException(status_code=409, detail="Item is not currently accepting bids")

    # --- The important part ---
    # This single call is what makes concurrent bids safe. Two bids arriving at
    # the same instant both hit this Lua script on the Redis server, which
    # processes them one at a time internally — only one can "win" the
    # compare-and-set, no matter how close together they arrive.
    accepted = try_place_bid(item_id, str(bid_in.amount_kes))
    if not accepted:
        raise HTTPException(
            status_code=409,
            detail="Bid rejected — a higher or equal bid was already placed",
        )

    bid = crud.create_bid(db, item_id, bid_in)

    # Notify anyone watching this item — forwarded live via the WebSocket
    # in app/routers/ws.py, which subscribes to this same Redis channel.
    publish_event(item_id, {
        "type": "bid",
        "amount_kes": str(bid.amount_kes),
        "bidder_id": bid.bidder_id,
        "created_at": bid.created_at.isoformat(),
    })

    # --- Anti-sniping ---
    # If this bid landed within the last ANTI_SNIPE_WINDOW_SECONDS of the
    # auction's current end time, push the end time back by
    # ANTI_SNIPE_EXTENSION_SECONDS. This can happen repeatedly — every
    # last-second bid buys the auction a little more time, so a determined
    # bidder can't win just by waiting until the final instant.
    seconds_remaining = (item.ends_at - bid.created_at).total_seconds()
    if seconds_remaining <= ANTI_SNIPE_WINDOW_SECONDS:
        new_ends_at = item.ends_at + timedelta(seconds=ANTI_SNIPE_EXTENSION_SECONDS)
        crud.set_item_ends_at(db, item, new_ends_at)
        set_ends_at(item_id, new_ends_at.isoformat())

        publish_event(item_id, {
            "type": "extended",
            "new_ends_at": new_ends_at.isoformat(),
            "extended_by_seconds": ANTI_SNIPE_EXTENSION_SECONDS,
        })

    return bid


@router.get("", response_model=list[schemas.BidOut])
def list_bids(item_id: str, db: Session = Depends(get_db)):
    item = crud.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return crud.list_bids_for_item(db, item_id)
