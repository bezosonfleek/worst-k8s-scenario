import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getItem, placeBid } from "../api/client";
import { useItemSocket } from "../hooks/useItemSocket";
import { useCountdown, formatMs } from "../hooks/useCountdown";
import { useUser } from "../context/UserContext";
import CurrencyAmount from "../components/CurrencyAmount";

export default function ItemDetailPage() {
  const { itemId } = useParams();
  const { user } = useUser();
  const [item, setItem] = useState(null);
  const [bidAmount, setBidAmount] = useState("");
  const [bidError, setBidError] = useState(null);
  const [placing, setPlacing] = useState(false);

  useEffect(() => {
    getItem(itemId).then(setItem).catch((e) => setBidError(e.message));
  }, [itemId]);

  const { events, highestBidKes, endsAt, itemStatus, connected } = useItemSocket(itemId, {
    initialHighestBid: item?.highest_bid_kes,
    initialEndsAt: item?.ends_at,
  });

  const effectiveEndsAt = endsAt || item?.ends_at;
  const msLeft = useCountdown(effectiveEndsAt);
  const hasEnded = itemStatus?.startsWith("ended") || (item && msLeft <= 0 && item.status !== "pending" && item.status !== "rejected");

  async function handleBid(e) {
    e.preventDefault();
    setBidError(null);
    const amount = Number(bidAmount);
    if (!amount || amount <= 0) {
      setBidError("Enter a valid amount");
      return;
    }
    setPlacing(true);
    try {
      await placeBid(itemId, user.id, amount);
      setBidAmount("");
    } catch (err) {
      setBidError(err.message);
    } finally {
      setPlacing(false);
    }
  }

  if (!item) return <div className="page">Loading…</div>;

  const currentHighest = highestBidKes ?? item.highest_bid_kes ?? item.starting_price_kes;

  return (
    <div className="page item-detail">
      <h1>{item.title}</h1>
      {item.description && <p className="description">{item.description}</p>}
      {item.image_url && <img src={item.image_url} alt={item.title} className="item-image" />}

      <div className="auction-status">
        <div>
          <span className="label">Current highest bid</span>
          <div className="highest-bid">
            <CurrencyAmount amountKes={currentHighest} />
          </div>
        </div>
        <div>
          <span className="label">{hasEnded ? "Auction ended" : "Time left"}</span>
          <div className={`countdown ${!hasEnded && msLeft < 15000 ? "countdown-urgent" : ""}`}>
            {hasEnded ? "—" : formatMs(msLeft)}
          </div>
        </div>
      </div>

      {!connected && <p className="ws-status">Reconnecting to live updates…</p>}

      {hasEnded ? (
        <p className="ended-banner">
          This auction has ended. Winning bid:{" "}
          <CurrencyAmount amountKes={currentHighest} />
        </p>
      ) : (
        <form onSubmit={handleBid} className="bid-form">
          <input
            type="number"
            step="0.01"
            min="0"
            placeholder={`More than ${currentHighest} KES`}
            value={bidAmount}
            onChange={(e) => setBidAmount(e.target.value)}
          />
          <button type="submit" disabled={placing}>
            {placing ? "Placing…" : "Place Bid"}
          </button>
        </form>
      )}
      {bidError && <p className="error">{bidError}</p>}

      <h3>Live bid feed</h3>
      <ul className="bid-feed">
        {events
          .filter((e) => e.type === "bid")
          .slice()
          .reverse()
          .map((e, i) => (
            <li key={i}>
              <CurrencyAmount amountKes={e.amount_kes} /> — bidder {e.bidder_id.slice(0, 8)}
            </li>
          ))}
        {events.filter((e) => e.type === "extended").map((e, i) => (
          <li key={`ext-${i}`} className="extension-notice">
            ⏱ Auction extended by {e.extended_by_seconds}s (anti-snipe)
          </li>
        ))}
      </ul>
    </div>
  );
}
