from datetime import datetime
from sqlalchemy.orm import Session

from app import models, schemas


# ---------- Users ----------

def create_user(db: Session, user_in: schemas.UserCreate) -> models.User:
    user = models.User(display_name=user_in.display_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: str) -> models.User | None:
    return db.query(models.User).filter(models.User.id == user_id).first()


# ---------- Items ----------

def create_item(db: Session, item_in: schemas.ItemCreate) -> models.Item:
    item = models.Item(
        seller_id=item_in.seller_id,
        title=item_in.title,
        description=item_in.description,
        image_url=item_in.image_url,
        starting_price_kes=item_in.starting_price_kes,
        status=models.ItemStatus.pending,
        starts_at=item_in.starts_at,
        ends_at=item_in.ends_at,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_item(db: Session, item_id: str) -> models.Item | None:
    return db.query(models.Item).filter(models.Item.id == item_id).first()


def list_items(db: Session, status: models.ItemStatus | None = None) -> list[models.Item]:
    q = db.query(models.Item)
    if status is not None:
        q = q.filter(models.Item.status == status)
    return q.order_by(models.Item.created_at.desc()).all()


def update_item_status(db: Session, item: models.Item, new_status: models.ItemStatus) -> models.Item:
    item.status = new_status
    db.commit()
    db.refresh(item)
    return item


def set_item_ends_at(db: Session, item: models.Item, new_ends_at: datetime) -> models.Item:
    item.ends_at = new_ends_at
    db.commit()
    db.refresh(item)
    return item


def is_item_live(item: models.Item, now: datetime) -> bool:
    """An item is bid-able only if approved, past its start time, and before its end time."""
    return (
        item.status in (models.ItemStatus.approved, models.ItemStatus.live)
        and item.starts_at <= now < item.ends_at
    )


# ---------- Bids ----------

def create_bid(db: Session, item_id: str, bid_in: schemas.BidCreate) -> models.Bid:
    bid = models.Bid(item_id=item_id, bidder_id=bid_in.bidder_id, amount_kes=bid_in.amount_kes)
    db.add(bid)
    db.commit()
    db.refresh(bid)
    return bid


def list_bids_for_item(db: Session, item_id: str) -> list[models.Bid]:
    return (
        db.query(models.Bid)
        .filter(models.Bid.item_id == item_id)
        .order_by(models.Bid.amount_kes.desc())
        .all()
    )


def get_highest_bid_db(db: Session, item_id: str) -> models.Bid | None:
    return (
        db.query(models.Bid)
        .filter(models.Bid.item_id == item_id)
        .order_by(models.Bid.amount_kes.desc())
        .first()
    )
