from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db import Base,engine,SessionLocal
from app.api.routes import router
from app.services.seed import seed_demo_data

app=FastAPI(title="Debrecen Traffic Intelligence API",
 description="Traffic analytics, forecasting and anomaly detection using Debrecen EnCLOD data.",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=settings.allowed_origins,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
app.include_router(router)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db=SessionLocal()
    try: seed_demo_data(db)
    finally: db.close()

@app.get("/")
def root(): return {"message":"Debrecen Traffic Intelligence API","docs":"/docs","health":"/api/health"}
