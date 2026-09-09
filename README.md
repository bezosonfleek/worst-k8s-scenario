# PigaBid — Phases 1–8

Real-time auction platform: FastAPI + Postgres + Redis backend, React frontend.

## What's built

- **Phase 1** — Postgres models (`User`, `Item`, `Bid`) + Alembic migrations
- **Phase 2** — CRUD endpoints (list, view, seller creates, admin approves/rejects)
- **Phase 3** — Redis atomic bid safety (Lua compare-and-set) + pub/sub
- **Phase 4** — WebSocket (`/ws/items/{id}`) bridging Redis pub/sub to connected browsers, with auto-reconnect
- **Phase 5** — Anti-sniping: a bid within `ANTI_SNIPE_WINDOW_SECONDS` (default 30s) of the end time pushes it back by `ANTI_SNIPE_EXTENSION_SECONDS` (default 30s), repeatedly
- **Phase 6** — Background task auto-transitions `approved → live → ended_sold/ended_unsold` based on `starts_at`/`ends_at`
- **Phase 7** — React (Vite) frontend: item list, item detail (live countdown + bid feed + bid form), seller listing form, admin approval queue
- **Phase 8** — Currency display layer: bids always stored/compared in KES; `/fx/convert` gives a display-only conversion, cached in Redis

## Run everything

```bash
docker-compose up --build
```

First time only, apply migrations:
```bash
docker-compose exec api alembic upgrade head
```

- API: `http://localhost:8000` (docs at `/docs`)
- Frontend: `http://localhost:3000`

## Architecture

```
Frontend (React, nginx)  ──HTTP+WS──▶  API (FastAPI)
                                          │
                                   ┌──────┴──────┐
                                   │             │
                              Postgres        Redis
                          (durable data)  (bid race-safety,
                                           pub/sub, FX cache)
```

- **Postgres**: source of truth — users, items, bids, final results.
- **Redis**: (1) atomic highest-bid check via a Lua script, so two simultaneous bids can never both "win"; (2) pub/sub channel per item (`item:{id}:events`), consumed by the WebSocket layer; (3) FX rate cache.
- **Background tasks** (in the API process): `redis_listener` forwards pub/sub → WebSocket clients; `auction_closer_loop` polls every `AUCTION_CLOSER_POLL_SECONDS` (default 5s) to start/close auctions on schedule.

## Manual test flow

1. `POST /users` — create a seller, an admin, a couple of bidders.
2. Flip `is_admin=true` for your admin user directly in Postgres (no self-serve admin signup by design — no real auth yet).
3. `POST /items` — seller creates a listing (`pending`).
4. `PATCH /items/{id}/status?acting_user_id={admin_id}` — admin approves (seeds Redis with starting price).
5. Open the item in the frontend, or connect to `ws://localhost:8000/ws/items/{id}` directly, and place bids via `POST /items/{id}/bids`.
6. Watch: bids broadcast live, last-second bids extend the countdown, and the auction auto-closes with the correct winner once `ends_at` passes.

## Known gaps (intentional, deferred)

- **No real auth** — `acting_user_id`/`bidder_id`/`seller_id` are passed as plain identifiers, not verified via session/JWT. Fine for proving the flow; replace before anything public-facing.
- **No proxy/max-bid auto-bidding** — explicitly deferred per design discussion.
- **FX conversion requires outbound internet** to `api.exchangerate-api.com` — swap the URL in `app/fx.py` if you need a different provider.
- **No k8s manifests yet** — that's Phase 9, along with Trivy scanning in CI.

## Environment variables (API)

| Var | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql://pigabid:pigabid@localhost:5432/pigabid` | Postgres connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `FRONTEND_ORIGINS` | `http://localhost:5173,http://localhost:3000` | CORS allow-list, comma-separated |
| `ANTI_SNIPE_WINDOW_SECONDS` | `30` | Anti-snipe trigger window |
| `ANTI_SNIPE_EXTENSION_SECONDS` | `30` | Anti-snipe extension amount |
| `AUCTION_CLOSER_POLL_SECONDS` | `5` | How often the background closer checks for started/ended auctions |
| `FX_RATE_CACHE_TTL_SECONDS` | `3600` | How long FX rates are cached in Redis |

## Frontend env

`frontend/.env` sets `VITE_API_URL` for local dev. In Docker, it's baked in at build time via `--build-arg VITE_API_URL=...` (see `frontend/Dockerfile` and `docker-compose.yml`).
