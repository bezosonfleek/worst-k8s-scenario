// In dev, Vite reads VITE_API_URL from .env / .env.local.
// In prod, this gets baked in at build time (see Dockerfile for the frontend).
export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
export const WS_URL = API_URL.replace(/^http/, "ws");
