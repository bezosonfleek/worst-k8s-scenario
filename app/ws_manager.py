import asyncio
import json
from fastapi import WebSocket

from app.redis_client import r as redis_client, events_channel


class ConnectionManager:
    """
    Tracks which WebSocket connections are watching which item, and forwards
    Redis pub/sub messages to the right sockets. One manager instance lives
    for the whole app process (see main.py).
    """

    def __init__(self):
        # item_id -> set of connected websockets watching that item
        self.connections: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, item_id: str, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.connections.setdefault(item_id, set()).add(websocket)

    async def disconnect(self, item_id: str, websocket: WebSocket):
        async with self._lock:
            conns = self.connections.get(item_id)
            if conns is not None:
                conns.discard(websocket)
                if not conns:
                    del self.connections[item_id]

    async def broadcast(self, item_id: str, message: dict):
        conns = self.connections.get(item_id, set())
        dead = []
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(item_id, ws)


manager = ConnectionManager()


async def redis_listener():
    """
    Background task (started once at app startup) that subscribes to ALL
    item event channels via a Redis pattern subscription, and forwards each
    message to whichever local WebSocket clients are watching that item.

    One Redis connection handles every item's events — we don't open a new
    subscription per item, we just pattern-match "item:*:events" and use the
    channel name to figure out which item_id a message belongs to.

    Wrapped in an outer retry loop: if Redis is temporarily unreachable
    (restart, network blip), this reconnects with a short backoff instead of
    dying silently and leaving every WebSocket client stuck with no updates.
    """
    loop = asyncio.get_event_loop()

    while True:
        try:
            pubsub = redis_client.pubsub()
            pubsub.psubscribe("item:*:events")
            print("[redis_listener] subscribed to item:*:events")

            while True:
                # get_message is blocking/sync on the redis-py client; run it
                # in a thread so it doesn't block FastAPI's event loop.
                message = await loop.run_in_executor(
                    None, lambda: pubsub.get_message(timeout=1.0)
                )
                if message is None:
                    await asyncio.sleep(0.01)
                    continue
                if message["type"] != "pmessage":
                    continue

                channel = message["channel"]  # e.g. "item:<uuid>:events"
                try:
                    item_id = channel.split(":")[1]
                except IndexError:
                    continue

                try:
                    payload = json.loads(message["data"])
                except (json.JSONDecodeError, TypeError):
                    continue

                await manager.broadcast(item_id, payload)

        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"[redis_listener] lost connection ({e}), retrying in 2s")
            await asyncio.sleep(2)
