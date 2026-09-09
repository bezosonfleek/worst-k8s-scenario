import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Numeric, Enum as SAEnum, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class ItemStatus(str, enum.Enum):
    pending = "pending"      # awaiting admin approval
    approved = "approved"    # approved, waiting for starts_at
    live = "live"             # currently accepting bids
    rejected = "rejected"    # admin rejected the listing
    ended_sold = "ended_sold"      # auction ended, had a winning bid
    ended_unsold = "ended_unsold"  # auction ended, no bids


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    display_name = Column(String(80), nullable=False, unique=True)
    is_admin = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    items = relationship("Item", back_populates="seller", foreign_keys="Item.seller_id")
    bids = relationship("Bid", back_populates="bidder")


class Item(Base):
    __tablename__ = "items"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    seller_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)

    title = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)

    # All monetary values stored in KES regardless of display currency (see design notes).
    starting_price_kes = Column(Numeric(12, 2), nullable=False)

    status = Column(SAEnum(ItemStatus), nullable=False, default=ItemStatus.pending)

    starts_at = Column(DateTime, nullable=False)   # scheduled start
    ends_at = Column(DateTime, nullable=False)      # can be pushed later by anti-snipe extensions

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    seller = relationship("User", back_populates="items", foreign_keys=[seller_id])
    bids = relationship("Bid", back_populates="item", order_by="Bid.amount_kes.desc()")


class Bid(Base):
    __tablename__ = "bids"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    item_id = Column(UUID(as_uuid=False), ForeignKey("items.id"), nullable=False)
    bidder_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)

    amount_kes = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    item = relationship("Item", back_populates="bids")
    bidder = relationship("User", back_populates="bids")
