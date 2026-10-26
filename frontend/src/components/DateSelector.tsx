import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { formatDeliveryDate, isValidJanuary2026 } from "../utils/format";

export const DEFAULT_DATE = "2026-01-15";

function shift(date: string, days: number): string {
  const d = new Date(`${date}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  const next = d.toISOString().slice(0, 10);
  return isValidJanuary2026(next) ? next : date;
}

export function DateSelector({
  value,
  onChange,
}: {
  value: string;
  onChange: (date: string) => void;
}) {
  const [draft, setDraft] = useState(value);
  const commit = (next: string) => {
    setDraft(next);
    if (isValidJanuary2026(next)) onChange(next);
  };
  return (
    <div className="date-selector">
      <button
        type="button"
        className="btn btn-icon"
        aria-label="Previous day"
        disabled={value <= "2026-01-01"}
        onClick={() => commit(shift(value, -1))}
      >
        <ChevronLeft size={16} aria-hidden />
      </button>
      <div className="date-field">
        <label htmlFor="delivery-date">Delivery date</label>
        <input
          id="delivery-date"
          type="date"
          min="2026-01-01"
          max="2026-01-31"
          value={draft}
          onChange={(e) => commit(e.target.value)}
        />
        <span className="date-pretty">{formatDeliveryDate(value)}</span>
      </div>
      <button
        type="button"
        className="btn btn-icon"
        aria-label="Next day"
        disabled={value >= "2026-01-31"}
        onClick={() => commit(shift(value, 1))}
      >
        <ChevronRight size={16} aria-hidden />
      </button>
    </div>
  );
}
