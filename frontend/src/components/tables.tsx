import { useMemo, useState } from "react";
import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import type {
  AccuracyResponse,
  ForecastResponse,
} from "../types/api";
import {
  formatAgeHours,
  formatDateTimeUTC,
  formatMw,
  formatPercent,
  formatTimeHHMM,
} from "../utils/format";

const LARGE_ERROR_MW = 1500;

type SortKey = "time" | "error" | "ape";

export function ForecastTable({ data }: { data: ForecastResponse }) {
  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th scope="col">Delivery time</th>
            <th scope="col" className="num">Forecast (MW)</th>
            <th scope="col">Forecast published</th>
            <th scope="col" className="num">Age at cutoff</th>
          </tr>
        </thead>
        <tbody>
          {data.observations.map((o) => (
            <tr key={o.startTime}>
              <td>
                {formatTimeHHMM(o.startTime)}{" "}
                <span className="muted">UTC</span>
              </td>
              <td className="num">{formatMw(o.forecastMw)}</td>
              <td>{formatDateTimeUTC(o.publishTime)}</td>
              <td className="num">{formatAgeHours(o.ageHours)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="table-note">
        {data.observations.length} intervals shown. All times UTC (UK was on GMT
        in January 2026). Age = decision cutoff minus publication time.
      </p>
    </div>
  );
}

export function AccuracyTable({ data }: { data: AccuracyResponse }) {
  const [sortKey, setSortKey] = useState<SortKey>("time");
  const [desc, setDesc] = useState(false);

  const rows = useMemo(() => {
    const copy = [...data.rows];
    const dir = desc ? -1 : 1;
    copy.sort((a, b) => {
      if (sortKey === "time") return dir * a.startTime.localeCompare(b.startTime);
      if (sortKey === "error")
        return dir * (Math.abs(a.errorMw) - Math.abs(b.errorMw));
      return (
        dir *
        ((a.absolutePercentageError ?? -1) - (b.absolutePercentageError ?? -1))
      );
    });
    return copy;
  }, [data.rows, sortKey, desc]);

  const toggle = (key: SortKey) => {
    if (key === sortKey) setDesc((d) => !d);
    else {
      setSortKey(key);
      setDesc(key !== "time");
    }
  };

  const header = (label: string, key: SortKey | null, numeric = false) => (
    <th scope="col" className={numeric ? "num" : ""}>
      {key ? (
        <button
          type="button"
          className="th-sort"
          onClick={() => toggle(key)}
          aria-label={`Sort by ${label}`}
        >
          {label}
          {sortKey === key ? (
            desc ? <ArrowDown size={13} aria-hidden /> : <ArrowUp size={13} aria-hidden />
          ) : (
            <ArrowUpDown size={13} aria-hidden className="muted" />
          )}
        </button>
      ) : (
        label
      )}
    </th>
  );

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            {header("Delivery time", "time")}
            {header("Forecast (MW)", null, true)}
            {header("Actual (MW)", null, true)}
            {header("Error (MW)", "error", true)}
            {header("Abs. error (MW)", null, true)}
            {header("Abs. % err.", "ape", true)}
            {header("Forecast published", null)}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => {
            const large = Math.abs(r.errorMw) >= LARGE_ERROR_MW;
            return (
              <tr key={r.startTime} className={large ? "row-warn" : undefined}>
                <td>
                  {formatTimeHHMM(r.startTime)} <span className="muted">UTC</span>
                </td>
                <td className="num">{formatMw(r.forecastMw)}</td>
                <td className="num">{formatMw(r.actualMw)}</td>
                <td className={`num ${r.errorMw > 0 ? "up" : r.errorMw < 0 ? "down" : ""}`}>
                  {r.errorMw > 0 ? "+" : ""}
                  {formatMw(r.errorMw)}
                </td>
                <td className="num">{formatMw(r.absoluteErrorMw)}</td>
                <td className="num">
                  {r.absolutePercentageError === null
                    ? <span className="muted" title="Actual generation was zero">n/a</span>
                    : formatPercent(r.absolutePercentageError)}
                </td>
                <td>{formatDateTimeUTC(r.publishTime)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="table-note">
        Error = forecast − actual. Rows with |error| ≥{" "}
        {LARGE_ERROR_MW.toLocaleString("en-GB")} MW are highlighted. “n/a” means
        actual generation was zero, so a percentage error is undefined.
      </p>
    </div>
  );
}
