from datetime import timedelta
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from app.models import TrafficObservation

def observations_frame(db):
    rows=db.query(TrafficObservation).order_by(TrafficObservation.timestamp.asc()).all()
    if not rows: return pd.DataFrame(columns=["timestamp","vehicles"])
    frame=pd.DataFrame([{"timestamp":r.timestamp,"vehicles":r.vehicle_count} for r in rows])
    return frame.groupby("timestamp",as_index=False)["vehicles"].sum().sort_values("timestamp")

def forecast(db,horizon=24):
    frame=observations_frame(db)
    if frame.empty: return []
    frame["timestamp"]=pd.to_datetime(frame["timestamp"])
    frame=frame.groupby("timestamp",as_index=False)["vehicles"].sum().sort_values("timestamp")
    frame["hour"]=frame.timestamp.dt.hour
    frame["weekday"]=frame.timestamp.dt.dayofweek
    frame["weekend"]=(frame.weekday>=5).astype(int)
    frame["lag1"]=frame.vehicles.shift(1)
    frame["lag24"]=frame.vehicles.shift(24)
    train=frame.dropna().reset_index(drop=True)
    last=frame.timestamp.max()
    output=[]
    if len(train)>=72:
        features=["hour","weekday","weekend","lag1","lag24"]
        model=RandomForestRegressor(n_estimators=120,max_depth=8,min_samples_leaf=2,random_state=42)
        model.fit(train[features],train.vehicles)
        history=list(frame.vehicles.astype(float))
        method="RandomForestRegressor"
        for step in range(1,horizon+1):
            ts=last+timedelta(hours=step)
            row=pd.DataFrame([{"hour":ts.hour,"weekday":ts.dayofweek,"weekend":int(ts.dayofweek>=5),
                "lag1":history[-1],"lag24":history[-24] if len(history)>=24 else history[-1]}])
            value=max(0,float(model.predict(row)[0])); history.append(value)
            output.append({"timestamp":ts.to_pydatetime(),"predicted_vehicles":round(value,1),"method":method})
    else:
        means=frame.groupby("hour").vehicles.mean().to_dict()
        for step in range(1,horizon+1):
            ts=last+timedelta(hours=step); value=float(means.get(ts.hour,frame.vehicles.mean()))
            output.append({"timestamp":ts.to_pydatetime(),"predicted_vehicles":round(max(0,value),1),"method":"hour-of-day seasonal baseline"})
    return output

def detect_anomalies(db):
    rows=db.query(TrafficObservation).order_by(TrafficObservation.timestamp.asc()).all()
    if not rows: return []
    frame=pd.DataFrame([{"timestamp":r.timestamp,"sensor_id":r.sensor_id,"vehicle_count":r.vehicle_count} for r in rows])
    found=[]
    for sensor,group in frame.groupby("sensor_id"):
        group=group.sort_values("timestamp").copy()
        values=group[["vehicle_count"]].astype(float)
        if len(group)>=30:
            model=IsolationForest(contamination=.04,random_state=42)
            labels=model.fit_predict(values); scores=model.decision_function(values)
            for i,label in enumerate(labels):
                if label==-1:
                    found.append({"timestamp":group.iloc[i].timestamp,"sensor_id":sensor,"vehicle_count":int(group.iloc[i].vehicle_count),
                        "score":round(float(-scores[i]),4),"reason":"Isolation Forest: unusual count for this sensor"})
        else:
            med=float(values.vehicle_count.median()); mad=float(np.median(np.abs(values.vehicle_count-med))) or 1
            for _,r in group.iterrows():
                score=abs(float(r.vehicle_count)-med)/(1.4826*mad)
                if score>=3.5: found.append({"timestamp":r.timestamp,"sensor_id":sensor,"vehicle_count":int(r.vehicle_count),
                    "score":round(score,3),"reason":"Robust median/MAD threshold"})
    return sorted(found,key=lambda x:x["score"],reverse=True)[:30]
