import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, api } from "../services/api";
import type {
  AccuracyResponse,
  ActualsResponse,
  ForecastResponse,
} from "../types/api";

export type LoadStatus = "idle" | "loading" | "ready" | "error";

interface Snapshot {
  forecast: ForecastResponse;
  actuals: ActualsResponse;
  accuracy: AccuracyResponse;
}

interface DeliveryData {
  forecast: ForecastResponse | null;
  actuals: ActualsResponse | null;
  accuracy: AccuracyResponse | null;
  status: LoadStatus;
  error: string | null;
  reload: () => void;
  backendDown: boolean;
}

/**
 * Fetches all dashboard data for one delivery date. A monotonically
 * increasing request id guarantees stale responses never overwrite newer
 * date selections; AbortController cancels in-flight requests on change.
 * State is only set inside async callbacks, never in the effect body.
 */
export function useDeliveryData(deliveryDate: string): DeliveryData {
  const [nonce, setNonce] = useState(0);
  const key = `${deliveryDate}#${nonce}`;
  const [snapshots, setSnapshots] = useState<Record<string, Snapshot>>({});
  const [failures, setFailures] = useState<Record<string, string>>({});
  const requestId = useRef(0);

  const reload = useCallback(() => setNonce((n) => n + 1), []);

  useEffect(() => {
    const id = ++requestId.current;
    const controller = new AbortController();
    const requestKey = key;

    (async () => {
      try {
        const [forecast, actuals, accuracy] = await Promise.all([
          api.forecasts(deliveryDate, controller.signal),
          api.actuals(deliveryDate, controller.signal),
          api.accuracy(deliveryDate, controller.signal),
        ]);
        if (requestId.current !== id || controller.signal.aborted) return;
        setSnapshots((prev) => ({ ...prev, [requestKey]: { forecast, actuals, accuracy } }));
      } catch (err) {
        if (controller.signal.aborted || requestId.current !== id) return;
        const message =
          err instanceof ApiError
            ? err.message
            : "Could not reach the backend. Is it running?";
        setFailures((prev) => ({ ...prev, [requestKey]: message }));
      }
    })();

    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  const snapshot = snapshots[key] ?? null;
  const failure = failures[key] ?? null;
  const status: LoadStatus = snapshot ? "ready" : failure ? "error" : "loading";

  return {
    forecast: snapshot?.forecast ?? null,
    actuals: snapshot?.actuals ?? null,
    accuracy: snapshot?.accuracy ?? null,
    status,
    error: failure,
    reload,
    backendDown:
      failure !== null &&
      /reach the backend|unavailable|Failed to fetch|Load failed/i.test(failure),
  };
}
