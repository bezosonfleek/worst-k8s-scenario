import asyncio
import contextlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import FRONTEND_ORIGINS
from app.routers import users, items, bids, ws, fx
from app.ws_manager import redis_listener
from app.closer import auction_closer_loop


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Two long-running background tasks for the whole app process:
    # 1. redis_listener — bridges Redis pub/sub -> connected WebSocket clients
    # 2. auction_closer_loop — periodically flips approved->live and closes
    #    ended auctions (Phase 6)
    listener_task = asyncio.create_task(redis_listener())
    closer_task = asyncio.create_task(auction_closer_loop())
    yield
    listener_task.cancel()
    closer_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await listener_task
    with contextlib.suppress(asyncio.CancelledError):
        await closer_task


app = FastAPI(title="PigaBid", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(items.router)
app.include_router(bids.router)
app.include_router(ws.router)
app.include_router(fx.router)


@app.get("/")
def read_root():
    return {"message": "PigaBid API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
