import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listItems } from "../api/client";
import CurrencyAmount from "../components/CurrencyAmount";

export default function ItemListPage() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        // Show both approved (scheduled/not-yet-started) and live items —
        // the item detail page's countdown makes clear which is which.
        const [approved, live] = await Promise.all([
          listItems("approved"),
          listItems("live"),
        ]);
        if (!cancelled) setItems([...approved, ...live]);
      } catch (err) {
        if (!cancelled) setError(err.message);
      }
    }
    load();
    const interval = setInterval(load, 10000); // light polling for list-level status changes
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="page">
      <h1>Live &amp; Upcoming Auctions</h1>
      {error && <p className="error">{error}</p>}
      {items.length === 0 && !error && <p>No auctions right now — check back soon.</p>}
      <div className="item-grid">
        {items.map((item) => (
          <Link to={`/items/${item.id}`} key={item.id} className="item-card">
            {item.image_url && <img src={item.image_url} alt={item.title} />}
            <h3>{item.title}</h3>
            <p className="item-status">{item.status}</p>
            <p>
              Starting: <CurrencyAmount amountKes={item.starting_price_kes} />
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}
