from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ws_manager import manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/items/{item_id}")
async def item_updates(websocket: WebSocket, item_id: str):
    """
    Connect here to receive live events for one item: new bids, anti-snipe
    time extensions, and auction-ended notifications. Messages are plain
    JSON, same shape as what's published in app/redis_client.py's
    publish_event(), e.g.:
        {"type": "bid", "amount_kes": "3500.00", "bidder_id": "...", "created_at": "..."}
        {"type": "extended", "new_ends_at": "...", "extended_by_seconds": 30}
        {"type": "ended", "status": "ended_sold", "winning_bid_kes": "3500.00"}
    """
    await manager.connect(item_id, websocket)
    try:
        while True:
            # We don't expect the client to send anything, but we need to
            # await something to detect disconnects promptly.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(item_id, websocket)
