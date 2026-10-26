/** Formatting helpers. All timestamps are UTC (UK was on GMT in Jan 2026). */

export function formatTimeHHMM(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  const h = String(d.getUTCHours()).padStart(2, "0");
  const m = String(d.getUTCMinutes()).padStart(2, "0");
  return `${h}:${m}`;
}

export function formatDateTimeUTC(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, "0")}-${String(
    d.getUTCDate(),
  ).padStart(2, "0")} ${formatTimeHHMM(iso)} UTC`;
}

export function formatDeliveryDate(isoDate: string): string {
  const [y, m, day] = isoDate.split("-").map(Number);
  const d = new Date(Date.UTC(y, m - 1, day));
  return d.toLocaleDateString("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });
}

export function formatMw(value: number | null | undefined, digits = 0): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toLocaleString("en-GB", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function formatPercent(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return `${value.toFixed(digits)}%`;
}

export function formatAgeHours(ageHours: number | null): string {
  if (ageHours === null || ageHours === undefined || Number.isNaN(ageHours))
    return "—";
  if (ageHours < 0) return "—";
  const h = Math.floor(ageHours);
  const m = Math.round((ageHours - h) * 60);
  if (h === 0) return `${m}m`;
  return `${h}h ${String(m).padStart(2, "0")}m`;
}

export function isValidJanuary2026(value: string): boolean {
  return /^\d{4}-\d{2}-\d{2}$/.test(value) && value >= "2026-01-01" && value <= "2026-01-31";
}
