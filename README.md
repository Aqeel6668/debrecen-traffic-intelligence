# Debrecen Traffic Intelligence

Full-stack portfolio app: FastAPI + React/TypeScript + PostgreSQL + scikit-learn.

## Quick start (SQLite, easiest)
1. Install Python 3.11+ and Node.js 20+.
2. Open `backend` in PyCharm, create a venv, install `requirements.txt`.
3. Copy `backend/.env.example` to `backend/.env`.
4. Run `uvicorn app.main:app --reload` from `backend`.
5. Open `http://127.0.0.1:8000/docs`.
6. In another terminal: `cd frontend && npm install && npm run dev`.
7. Open `http://localhost:5173`.

The backend seeds reproducible DEMO data on first launch. Press **Refresh data** to import public EnCLOD records. A failed external refresh does not replace existing data.

## PostgreSQL
From project root run `docker compose up -d db`. Change `DATABASE_URL` in `backend/.env` to:
`postgresql+psycopg://traffic:trafficpass@localhost:5432/trafficdb`
Restart backend.

## Data source
Public Traffic Debrecen - EnCLOD API:
`https://iot.citiq.cloud/portal/api/v2/view/traffic-debrecen-enclod/`
The integration requests hourly sums for the previous 30 days and normalizes supported JSON shapes. Public data refreshes hourly according to the portal documentation. Check current data terms before public deployment.

## API
- GET `/api/health`
- GET `/api/summary`
- GET `/api/timeseries?days=7`
- GET `/api/sensors`
- GET `/api/predictions?horizon=24`
- GET `/api/anomalies`
- POST `/api/refresh`
- POST `/api/ml/retrain`

## ML
Traffic target is the sum of sensor vehicle counts per hour. If at least 72 hourly rows are available, a RandomForestRegressor uses hour, weekday, weekend, and lagged values (1h and 24h). Otherwise the system uses a transparent hour-of-day average baseline. Anomaly detection uses IsolationForest when enough samples exist and median/MAD otherwise. These are portfolio estimates, not official traffic forecasts.

## Important map limitation
The public integration response does not supply verified GPS coordinates in this project. Map markers are explicitly illustrative city-area positions, not official sensor locations. Do not describe them as actual sensor GPS.

## Interview walkthrough
Trace data from `services/enclod.py` -> SQLAlchemy model -> FastAPI route -> frontend `api.ts` -> React chart. Explain chronological data, lag features, why time-series evaluation should not randomly shuffle rows, and why an anomaly is not necessarily an accident.
