import os
import json
import redis

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# ---- Key naming ----
# item:{id}:highest_bid   -> string, current highest bid amount in KES
# item:{id}:ends_at       -> string, ISO timestamp, mirrors DB (fast reads, no DB hit)
# item:{id}:events        -> pub/sub channel for live bid/extension events


def highest_bid_key(item_id: str) -> str:
    return f"item:{item_id}:highest_bid"


def ends_at_key(item_id: str) -> str:
    return f"item:{item_id}:ends_at"


def events_channel(item_id: str) -> str:
    return f"item:{item_id}:events"


# Atomic compare-and-set: only accept the bid if it's strictly higher than
# whatever is currently stored. Using a Lua script makes the "read current
# value, compare, write new value" sequence a single atomic operation on the
# Redis server — no race condition even if two bids arrive at the exact same
# millisecond from different API workers.
_PLACE_BID_LUA = """
local current = tonumber(redis.call('GET', KEYS[1]))
local new_amount = tonumber(ARGV[1])
if current == nil or new_amount > current then
    redis.call('SET', KEYS[1], ARGV[1])
    return 1
else
    return 0
end
"""
_place_bid_script = r.register_script(_PLACE_BID_LUA)


def try_place_bid(item_id: str, amount_kes: str) -> bool:
    """
    Attempts to set `amount_kes` as the new highest bid for `item_id`.
    Returns True if it was accepted (i.e. it was higher than the previous value),
    False if some other bid already matched or beat it.
    """
    result = _place_bid_script(keys=[highest_bid_key(item_id)], args=[amount_kes])
    return bool(result)


def get_highest_bid(item_id: str) -> str | None:
    return r.get(highest_bid_key(item_id))


def seed_highest_bid(item_id: str, starting_price_kes: str) -> None:
    """Called once when an item goes live, so Redis has a baseline to compare against."""
    r.set(highest_bid_key(item_id), starting_price_kes)


def set_ends_at(item_id: str, ends_at_iso: str) -> None:
    r.set(ends_at_key(item_id), ends_at_iso)


def get_ends_at(item_id: str) -> str | None:
    return r.get(ends_at_key(item_id))


def publish_event(item_id: str, event: dict) -> None:
    r.publish(events_channel(item_id), json.dumps(event))
