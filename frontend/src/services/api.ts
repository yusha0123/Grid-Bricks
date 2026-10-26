/** Reusable typed HTTP client for the FastAPI backend. */

import type {
  AccuracyResponse,
  ActualsResponse,
  ForecastResponse,
} from "../types/api";

const rawBaseUrl = import.meta.env.VITE_API_BASE_URL;
if (!rawBaseUrl || !rawBaseUrl.trim()) {
  throw new Error(
    "VITE_API_BASE_URL is not set. Add it to frontend/.env (see .env.example).",
  );
}
const BASE_URL = rawBaseUrl.trim().replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function get<T>(
  path: string,
  date: string,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(
    `${BASE_URL}${path}?date=${encodeURIComponent(date)}`,
    { signal },
  );
  if (!response.ok) {
    let detail = `Request failed (HTTP ${response.status})`;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      /* keep generic message */
    }
    throw new ApiError(response.status, detail);
  }
  return (await response.json()) as T;
}

export const api = {
  baseUrl: BASE_URL,
  forecasts: (date: string, signal?: AbortSignal) =>
    get<ForecastResponse>("/api/forecasts", date, signal),
  actuals: (date: string, signal?: AbortSignal) =>
    get<ActualsResponse>("/api/actuals", date, signal),
  accuracy: (date: string, signal?: AbortSignal) =>
    get<AccuracyResponse>("/api/accuracy", date, signal),
  health: async (signal?: AbortSignal): Promise<{ status: string }> => {
    const response = await fetch(`${BASE_URL}/api/health`, { signal });
    if (!response.ok)
      throw new ApiError(response.status, "Backend is unavailable");
    return (await response.json()) as { status: string };
  },
};
