import { useEffect, useState } from "react";
import { listItems, updateItemStatus } from "../api/client";
import { useUser } from "../context/UserContext";
import CurrencyAmount from "../components/CurrencyAmount";

export default function AdminQueuePage() {
  const { user } = useUser();
  const [pending, setPending] = useState([]);
  const [error, setError] = useState(null);
  const [actingOn, setActingOn] = useState(null);

  async function load() {
    try {
      setPending(await listItems("pending"));
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function act(itemId, status) {
    setActingOn(itemId);
    setError(null);
    try {
      await updateItemStatus(itemId, status, user.id);
      setPending((prev) => prev.filter((i) => i.id !== itemId));
    } catch (err) {
      setError(err.message);
    } finally {
      setActingOn(null);
    }
  }

  if (!user?.is_admin) {
    return (
      <div className="page">
        <h1>Admin</h1>
        <p>
          You don't have admin privileges. (No self-serve admin signup by design —
          this flag is set directly in the database for now.)
        </p>
      </div>
    );
  }

  return (
    <div className="page">
      <h1>Pending Listings</h1>
      {error && <p className="error">{error}</p>}
      {pending.length === 0 && <p>Nothing waiting for review.</p>}
      <div className="admin-queue">
        {pending.map((item) => (
          <div key={item.id} className="admin-queue-item">
            <div>
              <h3>{item.title}</h3>
              {item.description && <p>{item.description}</p>}
              <p>
                Starting price: <CurrencyAmount amountKes={item.starting_price_kes} />
              </p>
              <p className="meta">
                Starts: {new Date(item.starts_at).toLocaleString()} · Ends:{" "}
                {new Date(item.ends_at).toLocaleString()}
              </p>
            </div>
            <div className="admin-actions">
              <button
                disabled={actingOn === item.id}
                onClick={() => act(item.id, "approved")}
              >
                Approve
              </button>
              <button
                disabled={actingOn === item.id}
                className="reject"
                onClick={() => act(item.id, "rejected")}
              >
                Reject
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
