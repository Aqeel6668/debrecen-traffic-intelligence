# Debrecen Traffic Intelligence

A full-stack traffic monitoring system for Debrecen, Hungary, providing traffic analytics, visualizations, predictions, and anomaly detection using public EnCLOD data.

**Tech Stack:** React, TypeScript, FastAPI, Python, SQLite/PostgreSQL, Pandas, scikit-learn, Recharts, Leaflet.

## Run Locally

**Backend**
```bash
cd backend
python -m venv venv
pip install -r requirements.txt
# Copy .env.example to .env
uvicorn app.main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`  
API docs: `http://127.0.0.1:8000/docs`

## Limitations

Predictions are experimental estimates. Map markers are illustrative, not verified sensor locations.

**Data Source:** [EnCLOD – Traffic Debrecen](https://iot.citiq.cloud/portal/api/v2/view/traffic-debrecen-enclod/)