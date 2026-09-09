import { useEffect, useState } from "react";
import { convertCurrency } from "../api/client";

const CURRENCIES = ["KES", "USD", "EUR", "GBP"];

export default function CurrencyAmount({ amountKes }) {
  const [currency, setCurrency] = useState(
    () => localStorage.getItem("pigabid_display_currency") || "KES"
  );
  const [displayValue, setDisplayValue] = useState(amountKes);
  const [converting, setConverting] = useState(false);

  useEffect(() => {
    localStorage.setItem("pigabid_display_currency", currency);
    if (currency === "KES" || amountKes == null) {
      setDisplayValue(amountKes);
      return;
    }
    setConverting(true);
    convertCurrency(amountKes, currency)
      .then((res) => setDisplayValue(res.converted_amount))
      .catch(() => setDisplayValue(null)) // FX unavailable — fail quietly, don't block the UI
      .finally(() => setConverting(false));
  }, [amountKes, currency]);

  return (
    <span className="currency-amount">
      <strong>
        {displayValue != null ? Number(displayValue).toLocaleString() : "—"}
      </strong>{" "}
      <select value={currency} onChange={(e) => setCurrency(e.target.value)}>
        {CURRENCIES.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>
      {converting && <span className="fx-loading"> …</span>}
    </span>
  );
}
