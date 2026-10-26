import type { ReactNode } from "react";
import { AlertTriangle, Inbox, Loader2, RotateCw } from "lucide-react";

export function Card({
  title,
  subtitle,
  action,
  children,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="card">
      <div className="card-head">
        <div>
          <h2 className="card-title">{title}</h2>
          {subtitle && <p className="card-subtitle">{subtitle}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

export function MetricCard({
  label,
  value,
  sub,
  tone = "neutral",
}: {
  label: string;
  value: string;
  sub?: string;
  tone?: "neutral" | "good" | "warn" | "bad";
}) {
  return (
    <div className={`metric metric-${tone}`}>
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      {sub && <div className="metric-sub">{sub}</div>}
    </div>
  );
}

export function LoadingState({ message = "Loading data…" }: { message?: string }) {
  return (
    <div className="state" role="status" aria-live="polite">
      <Loader2 className="spin" size={22} aria-hidden />
      <p>{message}</p>
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div className="state state-error" role="alert">
      <AlertTriangle size={22} aria-hidden />
      <p className="state-title">Could not load data</p>
      <p className="state-detail">{message}</p>
      <button type="button" className="btn btn-primary" onClick={onRetry}>
        <RotateCw size={15} aria-hidden /> Retry
      </button>
    </div>
  );
}

export function EmptyState({
  title,
  detail,
}: {
  title: string;
  detail?: string;
}) {
  return (
    <div className="state" role="status">
      <Inbox size={22} aria-hidden />
      <p className="state-title">{title}</p>
      {detail && <p className="state-detail">{detail}</p>}
    </div>
  );
}
