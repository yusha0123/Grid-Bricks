import { ForecastChart } from "../components/charts";
import { ForecastTable } from "../components/tables";
import { Card, EmptyState, ErrorState, LoadingState, MetricCard } from "../components/ui";
import type { ForecastResponse } from "../types/api";
import { formatDateTimeUTC, formatMw } from "../utils/format";

export function ForecastPage({
  status,
  error,
  forecast,
  reload,
}: {
  status: "idle" | "loading" | "ready" | "error";
  error: string | null;
  forecast: ForecastResponse | null;
  reload: () => void;
}) {
  if (status === "loading" || status === "idle")
    return <LoadingState message="Loading day-ahead forecast…" />;
  if (status === "error")
    return <ErrorState message={error ?? "Unknown error"} onRetry={reload} />;
  if (!forecast || forecast.observations.length === 0)
    return (
      <EmptyState
        title="No forecast available for this delivery day"
        detail="No WINDFOR run was published before the decision cutoff. Try another date in January 2026."
      />
    );

  const s = forecast.summary;
  return (
    <div className="page-grid">
      <div className="metrics">
        <MetricCard
          label="Average forecast"
          value={`${formatMw(s.averageMw)} MW`}
          sub={`Across ${s.count} intervals`}
        />
        <MetricCard
          label="Maximum forecast"
          value={`${formatMw(s.maxMw)} MW`}
          sub="Peak interval"
        />
        <MetricCard
          label="Minimum forecast"
          value={`${formatMw(s.minMw)} MW`}
          sub="Lowest interval"
        />
        <MetricCard
          label="Forecast publication"
          value={
            s.latestPublishTime ? formatDateTimeUTC(s.latestPublishTime) : "—"
          }
          sub={
            s.distinctPublishTimes <= 1
              ? "Single run for all intervals"
              : `${s.distinctPublishTimes} distinct runs`
          }
          tone="good"
        />
      </div>

      <Card
        title="Forecast wind generation"
        subtitle={`Day-ahead forecast for the delivery day · ${forecast.observations.length} hourly intervals · MW`}
      >
        <ForecastChart data={forecast} />
      </Card>

      <Card
        title="Forecast details"
        subtitle={`Decision cutoff ${formatDateTimeUTC(forecast.decisionCutoff)} · ${forecast.missingIntervals.length} half-hour slots without an hourly forecast`}
      >
        <p className="info-box">{forecast.decisionCutoffExplanation}</p>
        <ForecastTable data={forecast} />
      </Card>
    </div>
  );
}
