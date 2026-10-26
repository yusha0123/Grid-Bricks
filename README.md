# Wind Power Analytics

Internal dashboard for a UK electricity utility's energy purchasing team.
It shows the national wind generation forecast that was available at the
day-ahead purchasing decision, compares it against actual wind generation,
and scores forecast accuracy — for delivery days in **January 2026**.

Data source: Elexon BMRS (national UK wind, `WINDFOR` forecasts and `FUELHH`
actuals with `fuelType=WIND`).

> AI assistance disclosure: this project was built with the help of an AI
> coding assistant (Muse Spark via OpenCode). All Elexon data shown is real
> data retrieved live from the Elexon API; no mock data is used at runtime.

## Product overview

- **Wind Forecast** — what wind generation was expected for the selected
  delivery day, based on the forecast available when the purchasing decision
  was made: summary cards (avg / max / min / publication), a forecast chart,
  and the underlying records table.
- **Forecast Accuracy** — how that forecast performed: forecast-vs-actual
  chart, MAE / RMSE / MAPE metrics, an error-by-interval chart, a sortable
  comparison table, and a data-driven interpretation sentence.

## Tech choices

- Backend: **Python + FastAPI + Pydantic**, async **`httpx`** client, stdlib
  datetimes. No database, no pandas/NumPy (unnecessary here), no background
  workers. Tests with **pytest** + FastAPI `TestClient`.
- Frontend: **React + TypeScript + Vite**, **Recharts** charts,
  **lucide-react** icons, hand-rolled CSS design system (no Tailwind —
  the scaffold had none and a small custom stylesheet keeps the build lean),
  plain `fetch` with a typed client + React hook (no TanStack Query — three
  endpoints did not justify the extra dependency).

## Project structure

```text
Grid-Bricks/
├── backend/
│   ├── main.py                 # FastAPI app, CORS, router
│   ├── requirements.txt
│   ├── app/
│   │   ├── config.py           # env-based settings (incl. decision cutoff)
│   │   ├── api/routes.py       # GET /api/health|forecasts|actuals|accuracy
│   │   ├── schemas/responses.py# Pydantic response models
│   │   ├── services/
│   │   │   ├── elexon_client.py   # async client + TTL cache + normalisation
│   │   │   ├── forecast_service.py# cutoff + day-ahead selection (pure)
│   │   │   └── accuracy_service.py# startTime matching + MAE/RMSE/MAPE (pure)
│   │   └── utils/datetime_utils.py# timestamp parsing, UTC handling
│   └── tests/                  # test_forecast_selection|accuracy|api
└── frontend/
    ├── .env / .env.example     # VITE_API_BASE_URL
    └── src/
        ├── components/         # ui, DateSelector, charts, tables
        ├── pages/              # ForecastPage, AccuracyPage
        ├── hooks/useDeliveryData.ts
        ├── services/api.ts     # typed fetch client
        ├── types/api.ts        # backend contract mirrors
        └── utils/format.ts
```

## Prerequisites

- Python 3.12 with the existing `backend/.venv`
- Node 20+ and npm
- Internet access to `https://data.elexon.co.uk` (live Elexon data)

## Backend setup & run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --port 8000
```

Interactive API docs: http://localhost:8000/docs

## Frontend setup & run

```powershell
cd frontend
npm install
npm run dev        # http://localhost:5173
```

The API base URL comes from `.env` (`VITE_API_BASE_URL=http://localhost:8000`).

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Frontend → backend URL |
| `ELEXON_BASE_URL` | `https://data.elexon.co.uk/bmrs/api/v1` | Elexon API root |
| `DECISION_CUTOFF_TIME_UTC` | `11:00` | Day-ahead cutoff (day −1, UTC) |
| `MIN/MAX_DELIVERY_DATE` | `2026-01-01` / `2026-01-31` | Allowed range |
| `CACHE_TTL_SECONDS` | `600` | In-memory cache TTL |
| `ALLOWED_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | CORS origins |

## API endpoints

- `GET /api/health` — liveness; never calls Elexon.
- `GET /api/forecasts?date=YYYY-MM-DD` — delivery day, decision cutoff,
  summary (avg/max/min/publication), selected hourly observations with age
  at cutoff, and half-hour slots with no forecast.
- `GET /api/actuals?date=YYYY-MM-DD` — 48 half-hourly national WIND
  observations (FUELHH).
- `GET /api/accuracy?date=YYYY-MM-DD` — rows matched on exact `startTime`,
  MAE/RMSE/MAPE metrics, MAPE note, and an interpretation sentence.

Dates outside January 2026 → `400`; Elexon failures → `502` with a message.

## Forecast decision-cutoff assumption

The purchasing team must use information available at the day-ahead
decision, not forecasts published later. Rule (uniform for every interval
of delivery day **D**):

1. Take all valid `WINDFOR` records for each `startTime`.
2. Keep only records with `publishTime ≤ (D−1) 11:00 UTC`.
3. Select the latest eligible `publishTime` per `startTime`
   (tie-break: highest generation — deterministic and documented).
4. Intervals with no eligible forecast are reported as unavailable
   (`missingIntervals`); later runs are never substituted.

**11:00 UTC on day −1 is an assumption for this analysis** (approximating the
UK day-ahead auction gate-closure window), not an official Elexon or market
rule. It is a named setting (`DECISION_CUTOFF_TIME_UTC` in
`backend/app/config.py`, `decision_cutoff_for()` in
`backend/app/services/forecast_service.py`) and can be changed without
touching selection logic.

## Accuracy metric definitions

- **MAE** = mean(|forecast − actual|) in MW
- **RMSE** = √mean((forecast − actual)²) in MW
- **MAPE** = mean(|forecast − actual| / actual) × 100 in %,
  **excluding intervals with zero actual generation** (`mapeCount` reports how
  many intervals were used)
- Matching is by exact (UTC-normalised) `startTime` only, never by array
  position; metrics are computed in the backend (`accuracy_service.py`).

## Timezone handling

Elexon timestamps carry explicit offsets and are parsed into aware UTC
datetimes (naive values are never compared with aware ones). The UI displays
UTC throughout; for January 2026 the UK is on GMT, so UTC equals UK local
time — stated in the UI/API rather than hardcoded as `Europe/London`.

## Data granularity note (verified against the live API)

- `WINDFOR` runs are **hourly** (`startTime` on the hour, ~8 runs/day).
- `FUELHH` actuals are **half-hourly** (48 settlement periods/day).
- Accuracy matching therefore yields up to 24 matched intervals/day; the
  half-hour actuals without an hourly forecast are listed as missing and
  never interpolated.

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests -q
```

21 tests, all offline (Elexon calls mocked): forecast selection (cutoff,
tie-breaks, timezones, empty), accuracy (MAE/RMSE/MAPE, zero-actual MAPE,
timestamp matching, empty set), and API contracts (health, validation,
endpoint shapes with a mocked client).

## Deployment (containerized)

Dockerfiles are provided for both apps, plus a compose file for local
containerized runs:

```powershell
docker compose up --build
```

- Backend: `http://localhost:8000` (uvicorn on `$PORT`)
- Frontend: `http://localhost:3000` (static build served by `serve`)

### Vercel

`vercel.json` registers both Dockerfiles via `@vercel/docker` and routes
`/api/*` to the backend container and everything else to the frontend
container. Set `VITE_API_BASE_URL` to your deployed backend URL at build
time and `ALLOWED_ORIGINS` to your frontend origin.

Note: Vercel's Docker builder runs containers as serverless functions with
cold starts and execution-time limits, and `@vercel/docker` is experimental.
For a simpler Vercel deployment, build the frontend as a static site and
deploy the backend as a Python serverless function; the Dockerfiles remain
useful for Render / Fly.io / Railway / local compose.

## Known limitations

- Elexon has no bulk-download here: each delivery day triggers a few
  date-filtered API calls (cached 10 min in memory). First load of a new
  date takes a few seconds.
- `WINDFOR` is hourly while actuals are half-hourly (see granularity note);
  the app matches exactly and reports coverage instead of interpolating.
- Production `dist/` bundle is ~650 kB (Recharts); acceptable for an
  internal dashboard, code-splitting not yet applied.
- Docker images were not built in this environment (Docker daemon not
  running at verification time); Dockerfiles follow standard, tested patterns.


- Elexon has no bulk-download here: each delivery day triggers a few
  date-filtered API calls (cached 10 min in memory). First load of a new
  date takes a few seconds.
- `WINDFOR` is hourly while actuals are half-hourly (see granularity note);
  the app matches exactly and reports coverage instead of interpolating.
- Production `dist/` bundle is ~650 kB (Recharts); acceptable for an
  internal dashboard, code-splitting not yet applied.
