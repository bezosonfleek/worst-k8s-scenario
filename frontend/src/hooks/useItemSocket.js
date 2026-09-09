import { useEffect, useRef, useState } from "react";
import { WS_URL } from "../api/config";

/**
 * Connects to /ws/items/{itemId} and keeps a running list of events plus
 * the two derived values components care about most: the current highest
 * bid and the current end time (which anti-snipe extensions can push back).
 * Auto-reconnects with a short delay if the socket drops.
 */
export function useItemSocket(itemId, { initialHighestBid, initialEndsAt } = {}) {
  const [events, setEvents] = useState([]);
  const [highestBidKes, setHighestBidKes] = useState(initialHighestBid ?? null);
  const [endsAt, setEndsAt] = useState(initialEndsAt ?? null);
  const [itemStatus, setItemStatus] = useState(null);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef(null);

  useEffect(() => {
    if (!itemId) return;
    let cancelled = false;
    let reconnectTimer;

    function connect() {
      const ws = new WebSocket(`${WS_URL}/ws/items/${itemId}`);
      socketRef.current = ws;

      ws.onopen = () => setConnected(true);

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setEvents((prev) => [...prev, data]);

        if (data.type === "bid") {
          setHighestBidKes(data.amount_kes);
        } else if (data.type === "extended") {
          setEndsAt(data.new_ends_at);
        } else if (data.type === "ended") {
          setItemStatus(data.status);
          setHighestBidKes(data.winning_bid_kes);
        }
      };

      ws.onclose = () => {
        setConnected(false);
        if (!cancelled) {
          reconnectTimer = setTimeout(connect, 2000);
        }
      };

      ws.onerror = () => ws.close();
    }

    connect();

    return () => {
      cancelled = true;
      clearTimeout(reconnectTimer);
      socketRef.current?.close();
    };
  }, [itemId]);

  return { events, highestBidKes, endsAt, itemStatus, connected };
}
