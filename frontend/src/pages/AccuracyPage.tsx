import {
  ForecastActualChart,
  ForecastErrorChart,
} from "../components/charts";
import { AccuracyTable } from "../components/tables";
import { Card, EmptyState, ErrorState, LoadingState, MetricCard } from "../components/ui";
import type { AccuracyResponse } from "../types/api";
import { formatDateTimeUTC, formatMw, formatPercent } from "../utils/format";

export function AccuracyPage({
  status,
  error,
  accuracy,
  reload,
}: {
  status: "idle" | "loading" | "ready" | "error";
  error: string | null;
  accuracy: AccuracyResponse | null;
  reload: () => void;
}) {
  if (status === "loading" || status === "idle")
    return <LoadingState message="Loading forecast accuracy…" />;
  if (status === "error")
    return <ErrorState message={error ?? "Unknown error"} onRetry={reload} />;
  if (!accuracy || accuracy.rows.length === 0)
    return (
      <EmptyState
        title="No matched observations for this delivery day"
        detail="Forecast and actual series share no delivery intervals. Try another date in January 2026."
      />
    );

  const m = accuracy.metrics;
  return (
    <div className="page-grid">
      <div className="metrics">
        <MetricCard
          label="MAE · mean absolute error"
          value={m.maeMw === null ? "—" : `${formatMw(m.maeMw)} MW`}
          sub={`${m.matchedCount} matched intervals`}
          tone={m.maeMw !== null && m.maeMw >= 1500 ? "warn" : "neutral"}
        />
        <MetricCard
          label="RMSE · root mean squared error"
          value={m.rmseMw === null ? "—" : `${formatMw(m.rmseMw)} MW`}
          sub="Penalises large errors"
        />
        <MetricCard
          label="MAPE · mean abs. % error"
          value={formatPercent(m.mapePercent)}
          sub={`${m.mapeCount} of ${m.matchedCount} intervals used`}
        />
        <MetricCard
          label="Mean error (bias)"
          value={
            m.meanErrorMw === null
              ? "—"
              : `${m.meanErrorMw > 0 ? "+" : ""}${formatMw(m.meanErrorMw)} MW`
          }
          sub={
            m.meanErrorMw === null
              ? undefined
              : m.meanErrorMw > 0
                ? "Forecast overestimated on average"
                : m.meanErrorMw < 0
                  ? "Forecast underestimated on average"
                  : "Unbiased on average"
          }
          tone={
            m.meanErrorMw === null
              ? "neutral"
              : Math.abs(m.meanErrorMw) >= 1000
                ? "warn"
                : "good"
          }
        />
      </div>

      {accuracy.interpretation && (
        <div className="interpretation" role="status">
          {accuracy.interpretation}
        </div>
      )}

      <Card
        title="Forecast vs actual generation"
        subtitle={`Matched on delivery start time · ${m.matchedCount} intervals · MW`}
      >
        <ForecastActualChart data={accuracy} />
      </Card>

      <Card
        title="Forecast error by interval"
        subtitle="Forecast − actual · positive = overestimate · MW"
      >
        <ForecastErrorChart data={accuracy} />
      </Card>

      <Card
        title="Interval comparison"
        subtitle={`Decision cutoff ${formatDateTimeUTC(accuracy.decisionCutoff)}`}
      >
        <p className="info-box">{accuracy.mapeNote} Matching uses exact delivery
        start times only — half-hourly actuals without an hourly forecast are
        excluded, never interpolated.</p>
        <AccuracyTable data={accuracy} />
      </Card>
    </div>
  );
}
