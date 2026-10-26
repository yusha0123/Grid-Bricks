import { useState } from "react";
import { Activity, ChartLine, WifiOff, Wind } from "lucide-react";
import { DateSelector, DEFAULT_DATE } from "./components/DateSelector";
import { useDeliveryData } from "./hooks/useDeliveryData";
import type { Section } from "./types/api";
import { formatDeliveryDate } from "./utils/format";
import { AccuracyPage } from "./pages/AccuracyPage";
import { ForecastPage } from "./pages/ForecastPage";

export default function App() {
  const [section, setSection] = useState<Section>("forecast");
  const [deliveryDate, setDeliveryDate] = useState(DEFAULT_DATE);
  const { forecast, accuracy, status, error, reload, backendDown } =
    useDeliveryData(deliveryDate);

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-icon" aria-hidden>
            <Wind size={20} />
          </span>
          <div>
            <h1>Wind Power Analytics</h1>
            <p>UK wind generation · Jan 2026</p>
          </div>
        </div>
        <nav className="nav" aria-label="Dashboard sections">
          <button
            type="button"
            className={section === "forecast" ? "nav-item active" : "nav-item"}
            onClick={() => setSection("forecast")}
            aria-current={section === "forecast" ? "page" : undefined}
          >
            <ChartLine size={16} aria-hidden /> Wind Forecast
          </button>
          <button
            type="button"
            className={section === "accuracy" ? "nav-item active" : "nav-item"}
            onClick={() => setSection("accuracy")}
            aria-current={section === "accuracy" ? "page" : undefined}
          >
            <Activity size={16} aria-hidden /> Forecast Accuracy
          </button>
        </nav>
        <div className="sidebar-foot">
          <DateSelector value={deliveryDate} onChange={setDeliveryDate} />
          <p className="data-status">
            <span
              className={`status-dot status-${status}`}
              aria-hidden
            />
            {status === "loading" && "Loading…"}
            {status === "ready" && `Data for ${formatDeliveryDate(deliveryDate)}`}
            {status === "error" && "Data unavailable"}
            {status === "idle" && "Waiting…"}
          </p>
          {backendDown && (
            <p className="backend-warn" role="alert">
              <WifiOff size={13} aria-hidden /> Backend unreachable — check that
              FastAPI runs on the configured URL.
            </p>
          )}
        </div>
      </aside>

      <main className="main">
        <header className="page-head">
          <div>
            <h2>
              {section === "forecast" ? "Wind Forecast" : "Forecast Accuracy"}
            </h2>
            <p className="page-sub">
              {section === "forecast"
                ? "What wind generation was expected, based on the forecast available at the day-ahead purchasing decision."
                : "How accurately the day-ahead forecast predicted actual wind generation."}
            </p>
          </div>
        </header>

        {section === "forecast" ? (
          <ForecastPage
            status={status}
            error={error}
            forecast={forecast}
            reload={reload}
          />
        ) : (
          <AccuracyPage
            status={status}
            error={error}
            accuracy={accuracy}
            reload={reload}
          />
        )}
      </main>
    </div>
  );
}
