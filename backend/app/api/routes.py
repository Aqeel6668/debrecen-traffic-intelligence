
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import TrafficObservation, RefreshLog
from app.core.config import settings
from app.services.enclod import fetch_enclod_data
from app.services.ml import (
    forecast,
    detect_anomalies,
    observations_frame,
)


router = APIRouter(prefix="/api")


@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": "Debrecen Traffic Intelligence",
    }


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    count = (
        db.query(func.count(TrafficObservation.id)).scalar() or 0
    )

    total = (
        db.query(func.sum(TrafficObservation.vehicle_count)).scalar()
        or 0
    )

    sensors = (
        db.query(
            func.count(func.distinct(TrafficObservation.sensor_id))
        ).scalar()
        or 0
    )

    latest = db.query(
        func.max(TrafficObservation.timestamp)
    ).scalar()

    demo = (
        db.query(func.count(TrafficObservation.id))
        .filter(TrafficObservation.source == "demo")
        .scalar()
        or 0
    )

    mode = (
        "demo" if count and demo == count
        else ("mixed" if demo else "enclod")
    )

    return {
        "total_vehicles": int(total),
        "observations": int(count),
        "sensors": int(sensors),
        "average_per_observation": (
            round(total / count, 2) if count else 0
        ),
        "latest_timestamp": latest,
        "data_mode": mode,
    }


@router.get("/timeseries")
def timeseries(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    frame = observations_frame(db)

    if frame.empty:
        return []

    cutoff = datetime.utcnow() - timedelta(days=days)

    frame = (
        frame[frame.timestamp >= cutoff]
        .groupby("timestamp", as_index=False)
        .vehicles.sum()
    )

    return [
        {
            "timestamp": row.timestamp.to_pydatetime(),
            "vehicles": int(row.vehicles),
        }
        for row in frame.itertuples()
    ]


@router.get("/sensors")
def sensors(db: Session = Depends(get_db)):
    rows = (
        db.query(
            TrafficObservation.sensor_id,
            func.count(TrafficObservation.id).label("observations"),
            func.sum(TrafficObservation.vehicle_count).label("total"),
            func.avg(TrafficObservation.vehicle_count).label("average"),
        )
        .group_by(TrafficObservation.sensor_id)
        .all()
    )

    return [
        {
            "sensor_id": row.sensor_id,
            "observations": row.observations,
            "total_vehicles": int(row.total or 0),
            "average_vehicles": round(float(row.average or 0), 1),
        }
        for row in rows
    ]


@router.get("/predictions")
def predictions(
    horizon: int = Query(24, ge=1, le=72),
    db: Session = Depends(get_db),
):
    return forecast(db, horizon)


@router.get("/anomalies")
def anomalies(db: Session = Depends(get_db)):
    return detect_anomalies(db)


@router.post("/refresh")
def refresh(db: Session = Depends(get_db)):
    try:
        rows = fetch_enclod_data(settings.enclod_api_url)

        # Do not overwrite existing data if the API returns no records.
        if not rows:
            db.add(
                RefreshLog(
                    created_at=datetime.utcnow(),
                    status="no_data",
                    message="EnCLOD returned no observations.",
                    rows_imported=0,
                )
            )

            db.commit()

            return {
                "status": "no_data",
                "rows_received": 0,
                "rows_inserted": 0,
                "message": (
                    "EnCLOD returned no observations. "
                    "Existing dashboard data has been preserved."
                ),
            }

        inserted = 0

        for item in rows:
            exists = (
                db.query(TrafficObservation.id)
                .filter_by(
                    sensor_id=item["sensor_id"],
                    timestamp=item["timestamp"],
                )
                .first()
            )

            if not exists:
                db.add(TrafficObservation(**item))
                inserted += 1

        db.add(
            RefreshLog(
                created_at=datetime.utcnow(),
                status="success",
                message="EnCLOD import completed",
                rows_imported=inserted,
            )
        )

        db.commit()

        return {
            "status": "success",
            "rows_received": len(rows),
            "rows_inserted": inserted,
            "message": "Data refresh completed.",
        }

    except Exception as exc:
        db.rollback()

        db.add(
            RefreshLog(
                created_at=datetime.utcnow(),
                status="error",
                message=str(exc)[:490],
                rows_imported=0,
            )
        )

        db.commit()

        raise HTTPException(
            status_code=502,
            detail=f"Could not refresh EnCLOD data: {exc}",
        )


@router.post("/ml/retrain")
def retrain(db: Session = Depends(get_db)):
    points = forecast(db, 24)

    return {
        "status": "completed",
        "forecast_points_generated": len(points),
        "method": points[0]["method"] if points else "no data",
    }
