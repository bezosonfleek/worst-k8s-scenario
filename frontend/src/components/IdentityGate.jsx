import { useState } from "react";
import { useUser } from "../context/UserContext";

export default function IdentityGate({ children }) {
  const { user, loading, register } = useUser();
  const [name, setName] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  if (loading) return <div className="center-message">Loading…</div>;
  if (user) return children;

  async function handleSubmit(e) {
    e.preventDefault();
    if (!name.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await register(name.trim());
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="identity-gate">
      <h1>PigaBid</h1>
      <p>Pick a display name to start bidding or listing items.</p>
      <form onSubmit={handleSubmit}>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. wanjiru_k"
          maxLength={80}
        />
        <button type="submit" disabled={submitting}>
          {submitting ? "…" : "Continue"}
        </button>
      </form>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
