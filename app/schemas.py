from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.models import ItemStatus


# ---------- Users ----------

class UserCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    display_name: str
    is_admin: bool
    created_at: datetime


# ---------- Items ----------

class ItemCreate(BaseModel):
    seller_id: str
    title: str = Field(min_length=1, max_length=120)
    description: Optional[str] = None
    image_url: Optional[str] = None
    starting_price_kes: Decimal = Field(gt=0)
    starts_at: datetime
    ends_at: datetime


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    seller_id: str
    title: str
    description: Optional[str]
    image_url: Optional[str]
    starting_price_kes: Decimal
    status: ItemStatus
    starts_at: datetime
    ends_at: datetime
    created_at: datetime


class ItemStatusUpdate(BaseModel):
    status: ItemStatus  # used by admin to approve/reject


# ---------- Bids ----------

class BidCreate(BaseModel):
    bidder_id: str
    amount_kes: Decimal = Field(gt=0)


class BidOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    item_id: str
    bidder_id: str
    amount_kes: Decimal
    created_at: datetime


class ItemDetailOut(ItemOut):
    bids: list[BidOut] = []
    highest_bid_kes: Optional[Decimal] = None
