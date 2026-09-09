import os

# Anti-snipe rule: if a valid bid lands within this many seconds of the
# auction's current end time, the end time is pushed back by the extension
# amount (repeatedly, as many times as needed) — see app/routers/bids.py.
ANTI_SNIPE_WINDOW_SECONDS = int(os.environ.get("ANTI_SNIPE_WINDOW_SECONDS", 30))
ANTI_SNIPE_EXTENSION_SECONDS = int(os.environ.get("ANTI_SNIPE_EXTENSION_SECONDS", 30))

# How often the background closer task checks for auctions whose end time
# has passed (Phase 6).
AUCTION_CLOSER_POLL_SECONDS = int(os.environ.get("AUCTION_CLOSER_POLL_SECONDS", 5))

# Base currency all bids/prices are stored and compared in internally.
BASE_CURRENCY = "KES"

# FX rate cache TTL in Redis (Phase 8).
FX_RATE_CACHE_TTL_SECONDS = int(os.environ.get("FX_RATE_CACHE_TTL_SECONDS", 3600))

# CORS — the frontend's origin(s), comma-separated in env for flexibility.
FRONTEND_ORIGINS = os.environ.get(
    "FRONTEND_ORIGINS", "http://localhost:5173,http://localhost:3000"
).split(",")
