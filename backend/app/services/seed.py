from datetime import datetime, timedelta
import math, random
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models import TrafficObservation

def seed_demo_data(db: Session, hours: int = 24 * 21):
    if db.query(func.count(TrafficObservation.id)).scalar():
        return 0
    rng = random.Random(19)
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    sensors = ["DEB-SENSOR-01", "DEB-SENSOR-02", "DEB-SENSOR-03", "DEB-SENSOR-04"]
    rows = []
    for h in range(hours, -1, -1):
        ts = now - timedelta(hours=h)
        rush = 1.65 if ts.hour in range(7, 10) or ts.hour in range(15, 19) else 1.0
        weekend = 0.72 if ts.weekday() >= 5 else 1.0
        for i, sensor in enumerate(sensors):
            base = [38, 51, 29, 44][i]
            total = max(0, int((base + 18 * math.sin((ts.hour-7)*math.pi/12))*rush*weekend + rng.gauss(0,7)))
            cars, vans, trucks = int(total*.78), int(total*.12), int(total*.07)
            rows.append(TrafficObservation(sensor_id=sensor, timestamp=ts, vehicle_count=total,
                cars=cars, vans=vans, trucks=trucks, other=max(0,total-cars-vans-trucks), source="demo"))
    db.add_all(rows); db.commit()
    return len(rows)
