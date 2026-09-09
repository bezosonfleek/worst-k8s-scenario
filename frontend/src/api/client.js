import { API_URL } from "./config";

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail;
    try {
      detail = (await res.json()).detail;
    } catch {
      detail = res.statusText;
    }
    throw new Error(detail || `Request failed (${res.status})`);
  }
  if (res.status === 204) return null;
  return res.json();
}

// ---------- Users ----------
export const createUser = (display_name) =>
  request("/users", { method: "POST", body: JSON.stringify({ display_name }) });

export const getUser = (userId) => request(`/users/${userId}`);

// ---------- Items ----------
export const listItems = (status) =>
  request(`/items${status ? `?status=${status}` : ""}`);

export const getItem = (itemId) => request(`/items/${itemId}`);

export const createItem = (payload) =>
  request("/items", { method: "POST", body: JSON.stringify(payload) });

export const updateItemStatus = (itemId, status, actingUserId) =>
  request(`/items/${itemId}/status?acting_user_id=${actingUserId}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });

// ---------- Bids ----------
export const placeBid = (itemId, bidderId, amountKes) =>
  request(`/items/${itemId}/bids`, {
    method: "POST",
    body: JSON.stringify({ bidder_id: bidderId, amount_kes: amountKes }),
  });

export const listBids = (itemId) => request(`/items/${itemId}/bids`);

// ---------- FX ----------
export const convertCurrency = (amountKes, to) =>
  request(`/fx/convert?amount_kes=${amountKes}&to=${to}`);
