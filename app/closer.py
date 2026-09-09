import asyncio
from datetime import datetime

from app import models
from app.config import AUCTION_CLOSER_POLL_SECONDS
from app.database import SessionLocal
from app.redis_client import get_highest_bid, publish_event, seed_highest_bid


def _tick():
    """One pass: move approved->live items forward, close ended items."""
    db = SessionLocal()
    try:
        now = datetime.utcnow()

        # approved, past starts_at, not yet ended -> mark live (display-only
        # status flip; bidding is already allowed for 'approved' too via
        # crud.is_item_live, this just makes the item's status accurately
        # reflect reality for anyone querying/listing items).
        starting_now = (
            db.query(models.Item)
            .filter(
                models.Item.status == models.ItemStatus.approved,
                models.Item.starts_at <= now,
                models.Item.ends_at > now,
            )
            .all()
        )
        for item in starting_now:
            item.status = models.ItemStatus.live
            # Redis may not have been seeded yet if this is the first time
            # we're crossing starts_at — safe to seed again, it's idempotent
            # as long as no bid has been placed (seed only sets if absent
            # would be nicer, but for now this mirrors the approval-time seed).
            if get_highest_bid(str(item.id)) is None:
                seed_highest_bid(str(item.id), str(item.starting_price_kes))
        if starting_now:
            db.commit()

        # approved or live, past ends_at -> close it out
        ending_now = (
            db.query(models.Item)
            .filter(
                models.Item.status.in_([models.ItemStatus.approved, models.ItemStatus.live]),
                models.Item.ends_at <= now,
            )
            .all()
        )
        for item in ending_now:
            highest = get_highest_bid(str(item.id))
            if highest is not None and float(highest) > float(item.starting_price_kes):
                item.status = models.ItemStatus.ended_sold
            elif highest is not None:
                # highest_bid_kes equals starting price -> no actual bids were placed
                item.status = models.ItemStatus.ended_unsold
            else:
                item.status = models.ItemStatus.ended_unsold

            publish_event(str(item.id), {
                "type": "ended",
                "status": item.status.value,
                "winning_bid_kes": highest,
            })
        if ending_now:
            db.commit()
    finally:
        db.close()


async def auction_closer_loop():
    """Runs forever in the background (started at app startup, see main.py)."""
    while True:
        try:
            _tick()
        except Exception as e:
            # Don't let one bad tick kill the whole background loop.
            print(f"[auction_closer] error during tick: {e}")
        await asyncio.sleep(AUCTION_CLOSER_POLL_SECONDS)
