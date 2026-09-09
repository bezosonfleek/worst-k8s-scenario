import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createItem } from "../api/client";
import { useUser } from "../context/UserContext";

export default function CreateListingPage() {
  const { user } = useUser();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    title: "",
    description: "",
    image_url: "",
    starting_price_kes: "",
    starts_at: "",
    ends_at: "",
  });
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);

    if (!form.title.trim()) return setError("Title is required");
    if (!form.starting_price_kes || Number(form.starting_price_kes) <= 0)
      return setError("Starting price must be greater than 0");
    if (!form.starts_at || !form.ends_at) return setError("Start and end time are required");
    if (new Date(form.ends_at) <= new Date(form.starts_at))
      return setError("End time must be after start time");

    setSubmitting(true);
    try {
      await createItem({
        seller_id: user.id,
        title: form.title.trim(),
        description: form.description.trim() || null,
        image_url: form.image_url.trim() || null,
        starting_price_kes: Number(form.starting_price_kes),
        // datetime-local inputs give "YYYY-MM-DDTHH:mm" in local time;
        // the backend expects naive UTC ISO strings, so convert here.
        starts_at: new Date(form.starts_at).toISOString().slice(0, -1),
        ends_at: new Date(form.ends_at).toISOString().slice(0, -1),
      });
      setSubmitted(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  if (submitted) {
    return (
      <div className="page">
        <h1>Listing submitted</h1>
        <p>
          Your item is now <strong>pending admin approval</strong>. It'll appear in the
          auction list once approved.
        </p>
        <button onClick={() => navigate("/")}>Back to auctions</button>
      </div>
    );
  }

  return (
    <div className="page">
      <h1>List an Item</h1>
      <form onSubmit={handleSubmit} className="listing-form">
        <label>
          Title
          <input value={form.title} onChange={(e) => update("title", e.target.value)} maxLength={120} />
        </label>
        <label>
          Description
          <textarea
            value={form.description}
            onChange={(e) => update("description", e.target.value)}
            rows={3}
          />
        </label>
        <label>
          Image URL (optional)
          <input value={form.image_url} onChange={(e) => update("image_url", e.target.value)} />
        </label>
        <label>
          Starting price (KES)
          <input
            type="number"
            min="0"
            step="0.01"
            value={form.starting_price_kes}
            onChange={(e) => update("starting_price_kes", e.target.value)}
          />
        </label>
        <label>
          Starts at
          <input
            type="datetime-local"
            value={form.starts_at}
            onChange={(e) => update("starts_at", e.target.value)}
          />
        </label>
        <label>
          Ends at
          <input
            type="datetime-local"
            value={form.ends_at}
            onChange={(e) => update("ends_at", e.target.value)}
          />
        </label>
        <button type="submit" disabled={submitting}>
          {submitting ? "Submitting…" : "Submit for approval"}
        </button>
      </form>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
