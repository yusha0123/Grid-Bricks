import {
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Bar,
} from "recharts";
import type {
  AccuracyResponse,
  ForecastResponse,
} from "../types/api";
import {
  formatMw,
  formatTimeHHMM,
  formatDateTimeUTC,
} from "../utils/format";

const FORECAST_COLOR = "#2563eb";
const ACTUAL_COLOR = "#16a34a";

interface Point {
  t: string;
  label: string;
  [key: string]: string | number | undefined;
}

function forecastPoints(data: ForecastResponse): Point[] {
  return data.observations.map((o) => ({
    t: o.startTime,
    label: formatTimeHHMM(o.startTime),
    forecast: o.forecastMw,
    publishTime: o.publishTime,
  }));
}

function accuracyPoints(data: AccuracyResponse): Point[] {
  return data.rows.map((r) => ({
    t: r.startTime,
    label: formatTimeHHMM(r.startTime),
    forecast: r.forecastMw,
    actual: r.actualMw,
    error: Math.round(r.errorMw * 10) / 10,
    publishTime: r.publishTime,
  }));
}

function axisProps() {
  return {
    tick: { fontSize: 11, fill: "#64748b" },
    tickLine: false,
    axisLine: { stroke: "#e2e8f0" },
  };
}

function ForecastTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: Point }>;
}) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div className="tooltip">
      <div className="tooltip-title">{formatDateTimeUTC(String(p.t))}</div>
      <div className="tooltip-row">
        <span className="dot" style={{ background: FORECAST_COLOR }} />
        Forecast <strong>{formatMw(p.forecast as number)} MW</strong>
      </div>
      {p.publishTime && (
        <div className="tooltip-sub">
          Published {formatDateTimeUTC(String(p.publishTime))}
        </div>
      )}
    </div>
  );
}

function AccuracyTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: Point }>;
}) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  const error = p.error as number;
  return (
    <div className="tooltip">
      <div className="tooltip-title">{formatDateTimeUTC(String(p.t))}</div>
      <div className="tooltip-row">
        <span className="dot" style={{ background: FORECAST_COLOR }} />
        Forecast <strong>{formatMw(p.forecast as number)} MW</strong>
      </div>
      <div className="tooltip-row">
        <span className="dot" style={{ background: ACTUAL_COLOR }} />
        Actual <strong>{formatMw(p.actual as number)} MW</strong>
      </div>
      <div className="tooltip-row">
        Error{" "}
        <strong className={error > 0 ? "up" : error < 0 ? "down" : ""}>
          {error > 0 ? "+" : ""}
          {formatMw(error)} MW
        </strong>
      </div>
      {p.publishTime && (
        <div className="tooltip-sub">
          Forecast published {formatDateTimeUTC(String(p.publishTime))}
        </div>
      )}
    </div>
  );
}

export function ForecastChart({ data }: { data: ForecastResponse }) {
  const points = forecastPoints(data);
  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={points} margin={{ top: 8, right: 12, bottom: 26, left: 0 }}>
          <CartesianGrid stroke="#eef2f7" vertical={false} />
          <XAxis
            dataKey="label"
            {...axisProps()}
            interval={3}
            label={{ value: "Delivery time (UTC)", position: "bottom", offset: 4, fontSize: 11, fill: "#94a3b8" }}
          />
          <YAxis
            {...axisProps()}
            width={64}
            tickFormatter={(v: number) => v.toLocaleString("en-GB")}
            label={{ value: "MW", position: "insideTopLeft", fontSize: 11, fill: "#94a3b8" }}
          />
          <Tooltip content={<ForecastTooltip />} />
          <Line
            type="monotone"
            dataKey="forecast"
            name="Forecast (MW)"
            stroke={FORECAST_COLOR}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ForecastActualChart({ data }: { data: AccuracyResponse }) {
  const points = accuracyPoints(data);
  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={points} margin={{ top: 8, right: 12, bottom: 26, left: 0 }}>
          <CartesianGrid stroke="#eef2f7" vertical={false} />
          <XAxis
            dataKey="label"
            {...axisProps()}
            interval={3}
            label={{ value: "Delivery time (UTC)", position: "bottom", offset: 4, fontSize: 11, fill: "#94a3b8" }}
          />
          <YAxis
            {...axisProps()}
            width={64}
            tickFormatter={(v: number) => v.toLocaleString("en-GB")}
            label={{ value: "MW", position: "insideTopLeft", fontSize: 11, fill: "#94a3b8" }}
          />
          <Tooltip content={<AccuracyTooltip />} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line
            type="monotone"
            dataKey="forecast"
            name="Forecast (MW)"
            stroke={FORECAST_COLOR}
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="actual"
            name="Actual (MW)"
            stroke={ACTUAL_COLOR}
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ForecastErrorChart({ data }: { data: AccuracyResponse }) {
  const points = accuracyPoints(data);
  return (
    <div className="chart">
      <ResponsiveContainer width="100%" height={260}>
        <ComposedChart data={points} margin={{ top: 8, right: 12, bottom: 26, left: 0 }}>
          <CartesianGrid stroke="#eef2f7" vertical={false} />
          <XAxis
            dataKey="label"
            {...axisProps()}
            interval={3}
            label={{ value: "Delivery time (UTC)", position: "bottom", offset: 4, fontSize: 11, fill: "#94a3b8" }}
          />
          <YAxis
            {...axisProps()}
            width={64}
            tickFormatter={(v: number) => `${v >= 0 ? "+" : ""}${v.toLocaleString("en-GB")}`}
            label={{ value: "MW", position: "insideTopLeft", fontSize: 11, fill: "#94a3b8" }}
          />
          <Tooltip
            content={<AccuracyTooltip />}
            cursor={{ fill: "rgba(37, 99, 235, 0.06)" }}
          />
          <ReferenceLine y={0} stroke="#94a3b8" strokeDasharray="4 4" />
          <Bar dataKey="error" name="Forecast error (MW)" radius={[2, 2, 0, 0]}>
            {points.map((p) => (
              <Cell
                key={String(p.t)}
                fill={(p.error as number) >= 0 ? "#f59e0b" : "#2563eb"}
              />
            ))}
          </Bar>
        </ComposedChart>
      </ResponsiveContainer>
      <p className="chart-note">
        Forecast error = forecast − actual (MW). Amber bars: overestimate; blue
        bars: underestimate.
      </p>
    </div>
  );
}
