# F1-Agent-Website

F1 Live Race Companion is a full-stack Formula 1 analysis and prediction app built with FastAPI, FastF1, scikit-learn, and React. It pulls race data, computes standings and circuit history, and serves an interactive dashboard with telemetry, lap comparisons, and ML-based predictions.

## Stack

- Backend: FastAPI, FastF1, pandas, numpy, scikit-learn, SQLAlchemy, Supabase/Postgres
- Frontend: React + Vite, Tailwind CSS, Recharts
- Data: FastF1 cache plus SQLite in dev or Supabase Postgres in production

## Project Layout

- `backend/`: FastAPI API, FastF1 helpers, and ML pipeline
- `frontend/`: React dashboard UI

## Backend API

- `GET /api/schedule`
- `GET /api/race/{year}/{round}/results`
- `GET /api/race/{year}/{round}/telemetry?driver=VER`
- `GET /api/race/{year}/{round}/laptime-comparison?drivers=VER,HAM`
- `GET /api/driver/{driver_code}/season-stats?year=2024`
- `GET /api/standings/drivers?year=2024`
- `GET /api/standings/constructors?year=2024`
- `GET /api/predict/race/{year}/{round}`
- `GET /api/predict/qualifying/{year}/{round}`
- `GET /api/circuit/{circuit_key}/history`

## Database

The backend uses SQLAlchemy and can run against a local SQLite file by default. To use Supabase, point `DATABASE_URL` or `SUPABASE_DB_URL` at your Supabase Postgres connection string. The API will create an `analysis_snapshots` table and persist race results, standings, telemetry, and prediction payloads there.

## Run Locally

1. Install backend dependencies:

```bash
Set-Location backend
py -m pip install -r requirements.txt
```

2. Start the API:

```bash
py -m uvicorn app.main:app --reload --port 8000
```

3. Install frontend dependencies:

```bash
Set-Location ..\frontend
npm install
```

4. Start the dashboard:

```bash
npm run dev
```

5. Open `http://127.0.0.1:5174`.

If port 5174 is already in use, Vite will stop instead of silently choosing a different port.

## Supabase Setup

1. Create a Supabase project and copy the Postgres connection string from the database settings.
2. Put it in `backend/.env` as `DATABASE_URL=...` or `SUPABASE_DB_URL=...`.
3. Leave `AUTO_CREATE_TABLES=true` if you want the app to create the snapshot table on startup.

## Notes

- FastF1 cache is enabled automatically under `backend/cache` when the API starts.
- The frontend reads `VITE_API_BASE_URL` from `frontend/.env.local` if you want to point it at a remote API.
- When live FastF1 data is not available, the app falls back to lightweight sample data so the dashboard still renders.
- If the database is unavailable, the API still runs and skips persistence instead of failing startup.
