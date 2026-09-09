import { useEffect, useState } from "react";

export function useCountdown(targetIso) {
  const [msLeft, setMsLeft] = useState(() => diff(targetIso));

  useEffect(() => {
    setMsLeft(diff(targetIso));
    const id = setInterval(() => setMsLeft(diff(targetIso)), 1000);
    return () => clearInterval(id);
  }, [targetIso]);

  return msLeft;
}

function diff(targetIso) {
  if (!targetIso) return 0;
  // Backend sends naive UTC ISO strings (no timezone suffix) — append "Z"
  // so the browser parses them as UTC instead of local time.
  const iso = targetIso.endsWith("Z") ? targetIso : `${targetIso}Z`;
  return Math.max(0, new Date(iso).getTime() - Date.now());
}

export function formatMs(ms) {
  if (ms <= 0) return "00:00";
  const totalSeconds = Math.floor(ms / 1000);
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}
