from pathlib import Path
from fastapi.responses import StreamingResponse, FileResponse
"""FastAPI backend. Run: uvicorn main:app --reload"""
import csv
import io
import json
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import jwt
import pandas as pd
from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

import database as db
import generate_data
import predictor
import preprocess
import train_model
from config import *
from recommendations import recommend


def seed():
    db.init_db()
    if db.read_df("SELECT COUNT(*) AS n FROM readings").iloc[0, 0] == 0:
        if not CSV_PATH.exists():
            generate_data.generate(CSV_PATH)
        db.load_readings(preprocess.clean(pd.read_csv(CSV_PATH)))
    if not MODEL_PATH.exists():
        train_model.train()
    predictor.load(force=True)


@asynccontextmanager
async def lifespan(app):
    seed()
    yield


app = FastAPI(title="Campus Energy AI", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
                   allow_methods=["*"], allow_headers=["*"])
bearer = HTTPBearer()


# ---------- helpers ----------
def records(df: pd.DataFrame):
    return json.loads(df.to_json(orient="records"))


def current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    try:
        return jwt.decode(creds.credentials, SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Session expired. Please log in again.")


def latest_date():
    return db.read_df("SELECT MAX(date) AS d FROM readings").iloc[0, 0]


def capacity_of(room):
    return ROOMS.get(room, {}).get("capacity", DEFAULT_CAPACITY)


def day_before(d):
    return (pd.Timestamp(d) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")


def build_alerts(scored: pd.DataFrame, date: str):
    yd = db.read_df("SELECT room, hour, energy_kwh FROM readings WHERE date=?", (day_before(date),))
    ymap = {(r.room, int(r.hour)): float(r.energy_kwh) for r in yd.itertuples()}
    acts = db.read_df("SELECT * FROM actions WHERE date=?", (date,))
    amap = {(a.room, int(a.hour)): a for a in acts.itertuples()}
    out = []
    for r in scored[scored["is_alert"]].itertuples():
        act = amap.get((r.room, int(r.hour)))
        out.append({
            "room": r.room, "date": r.date, "hour": int(r.hour),
            "occupancy": int(r.occupancy), "devices_on": int(r.devices_on), "temperature": float(r.temperature),
            "current_kwh": float(r.energy_kwh), "normal_kwh": float(r.predicted),
            "severity": "high" if r.energy_kwh >= r.predicted * 1.6 else "medium",
            "message": f"Unusual energy consumption detected in {r.room}.",
            "recommendations": recommend(int(r.occupancy), int(r.devices_on), float(r.energy_kwh), float(r.temperature),
                                         capacity_of(r.room), ymap.get((r.room, int(r.hour)))),
            "action": None if act is None else {"after_kwh": act.after_kwh, "saved_kwh": act.saved_kwh, "co2_kg": act.co2_kg},
        })
    return sorted(out, key=lambda a: (a["action"] is not None, -(a["current_kwh"] - a["normal_kwh"])))


def total_saved(where="", params=()):
    r = db.read_df(f"SELECT COALESCE(SUM(saved_kwh),0) AS s, COALESCE(SUM(co2_kg),0) AS c FROM actions {where}", params).iloc[0]
    return round(float(r.s), 2), round(float(r.c), 2)


# ---------- auth ----------
class LoginIn(BaseModel):
    email: str
    password: str


@app.post("/login")
def login(body: LoginIn):
    u = db.read_df("SELECT * FROM users WHERE email=?", (body.email.strip().lower(),))
    if u.empty or u.iloc[0].password_hash != db.hash_password(body.password):
        raise HTTPException(401, "Wrong email or password.")
    exp = datetime.now(timezone.utc) + timedelta(hours=TOKEN_HOURS)
    return {"token": jwt.encode({"sub": body.email, "role": u.iloc[0].role, "exp": exp}, SECRET_KEY, algorithm="HS256"),
            "email": body.email}


# ---------- data ----------
@app.get("/rooms")
def rooms(_=Depends(current_user)):
    df = db.read_df("SELECT DISTINCT room FROM readings ORDER BY room")
    return [{"name": r, "capacity": capacity_of(r)} for r in df["room"]]


@app.get("/energy-data")
def energy_data(room: str, date: str | None = None, _=Depends(current_user)):
    date = date or latest_date()
    df = db.read_df("SELECT * FROM readings WHERE room=? AND date=? ORDER BY hour", (room, date))
    s = predictor.score(df)
    return {"date": date, "rows": records(s[["hour", "temperature", "occupancy", "devices_on", "energy_kwh", "predicted", "is_alert"]])}


@app.get("/status")
def status(_=Depends(current_user)):
    d = latest_date()
    df = db.read_df("""SELECT r.* FROM readings r
        JOIN (SELECT room, MAX(hour) h FROM readings WHERE date=? GROUP BY room) m ON r.room=m.room AND r.hour=m.h
        WHERE r.date=? ORDER BY r.room""", (d, d))
    s = predictor.score(df)
    alerts = {a["room"]: a for a in build_alerts(s, d)}
    out = []
    for r in s.itertuples():
        a = alerts.get(r.room)
        out.append({"room": r.room, "hour": int(r.hour), "occupancy": int(r.occupancy), "capacity": capacity_of(r.room),
                    "current_kwh": float(r.energy_kwh), "normal_kwh": float(r.predicted),
                    "status": "High Consumption" if r.is_alert else "Normal",
                    "recommendations": a["recommendations"] if a else []})
    return {"date": d, "rooms": out}


@app.get("/summary")
def summary(room: str | None = None, _=Depends(current_user)):
    d = latest_date()
    sql, params = "SELECT * FROM readings WHERE date=?", [d]
    if room:
        sql, params = sql + " AND room=?", [d, room]
    s = predictor.score(db.read_df(sql, tuple(params)))
    saved, co2 = total_saved()
    return {"date": d, "actual_kwh": round(float(s.energy_kwh.sum()), 2), "predicted_kwh": round(float(s.predicted.sum()), 2),
            "alerts": int(s.is_alert.sum()), "saved_kwh": saved, "co2_kg": co2}


@app.get("/analytics")
def analytics(room: str, _=Depends(current_user)):
    df = db.read_df("SELECT * FROM readings WHERE room=?", (room,))
    df["dow"] = pd.to_datetime(df["date"]).dt.dayofweek
    hourly = df.groupby("hour").agg(energy=("energy_kwh", "mean"), occupancy=("occupancy", "mean")).round(2).reset_index()
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    wk = df.groupby("dow").agg(energy=("energy_kwh", "mean")).round(2).reset_index()
    wk["day"] = wk["dow"].map(lambda i: names[i])
    top = df.sample(min(250, len(df)), random_state=1)[["occupancy", "energy_kwh"]]
    return {"hourly": records(hourly), "weekday": records(wk[["day", "energy"]]), "scatter": records(top)}


# ---------- prediction ----------
class PredictIn(BaseModel):
    room: str
    hour: int = Field(ge=0, le=23)
    day: int = Field(ge=0, le=6, description="0=Monday ... 6=Sunday")
    temperature: float = Field(ge=-10, le=60)
    occupancy: int = Field(ge=0, le=5000)
    prev_energy: float | None = Field(default=None, ge=0)


@app.post("/predict")
def predict(body: PredictIn, _=Depends(current_user)):
    if body.room not in predictor.load()["rooms"]:
        raise HTTPException(422, f"Unknown room: {body.room}")
    kwh = predictor.predict_one(body.room, body.hour, body.day, body.temperature, body.occupancy, body.prev_energy)
    return {"room": body.room, "predicted_kwh": round(kwh, 2),
            "estimated_cost_inr": round(kwh * COST_PER_KWH, 2), "estimated_co2_kg": round(kwh * EMISSION_FACTOR, 2)}


# ---------- alerts, recommendations, actions ----------
@app.get("/alerts")
def alerts(date: str | None = None, _=Depends(current_user)):
    date = date or latest_date()
    s = predictor.score(db.read_df("SELECT * FROM readings WHERE date=?", (date,)))
    return {"date": date, "alerts": build_alerts(s, date)}


@app.get("/recommendations")
def recommendations(date: str | None = None, _=Depends(current_user)):
    a = alerts(date)["alerts"]
    return [{"room": x["room"], "hour": x["hour"], "recommendations": x["recommendations"]} for x in a]


class ActionIn(BaseModel):
    room: str
    date: str
    hour: int = Field(ge=0, le=23)
    before_kwh: float = Field(ge=0)
    after_kwh: float = Field(ge=0)
    note: str = ""


@app.post("/actions")
def add_action(body: ActionIn, _=Depends(current_user)):
    saved = round(max(body.before_kwh - body.after_kwh, 0), 2)
    co2 = round(saved * EMISSION_FACTOR, 2)
    db.execute("DELETE FROM actions WHERE room=? AND date=? AND hour=?", (body.room, body.date, body.hour))
    db.execute("""INSERT INTO actions(room,date,hour,before_kwh,after_kwh,saved_kwh,co2_kg,note) VALUES (?,?,?,?,?,?,?,?)""",
               (body.room, body.date, body.hour, body.before_kwh, body.after_kwh, saved, co2, body.note))
    return {"saved_kwh": saved, "co2_kg": co2, "emission_factor": EMISSION_FACTOR}


class SpikeIn(BaseModel):
    room: str = "Computer Lab 1"


@app.post("/simulate-spike")
def simulate_spike(body: SpikeIn, _=Depends(current_user)):
    """Demo helper: overwrites the room's latest reading with 8 people, 40 devices on, high usage."""
    d = latest_date()
    r = db.read_df("SELECT MAX(hour) AS h FROM readings WHERE date=? AND room=?", (d, body.room)).iloc[0, 0]
    if pd.isna(r):
        raise HTTPException(404, "No readings for that room.")
    hour = int(r)
    dow = pd.Timestamp(d).dayofweek
    normal = predictor.predict_one(body.room, hour, dow, 31, 8)
    energy = round(max(normal + 4.2, 8.0), 2)
    db.execute("DELETE FROM readings WHERE date=? AND room=? AND hour=?", (d, body.room, hour))
    db.execute("INSERT INTO readings(date,hour,room,temperature,occupancy,devices_on,energy_kwh,prev_energy) VALUES (?,?,?,?,?,?,?,?)",
               (d, hour, body.room, 31, 8, 40, energy, normal))
    return {"room": body.room, "hour": hour, "energy_kwh": energy}


# ---------- reports ----------
def build_report(period: str):
    days = {"daily": 1, "weekly": 7, "monthly": 30}.get(period)
    if not days:
        raise HTTPException(404, "Unknown report type.")
    end = latest_date()
    start = (pd.Timestamp(end) - pd.Timedelta(days=days - 1)).strftime("%Y-%m-%d")
    s = predictor.score(db.read_df("SELECT * FROM readings WHERE date BETWEEN ? AND ?", (start, end)))
    by_day = s.groupby("date").agg(actual=("energy_kwh", "sum"), predicted=("predicted", "sum"),
                                   alerts=("is_alert", "sum")).round(2).reset_index()
    by_room = s.groupby("room").agg(actual=("energy_kwh", "sum"), predicted=("predicted", "sum"),
                                    alerts=("is_alert", "sum")).round(2).reset_index()
    saved, co2 = total_saved("WHERE date BETWEEN ? AND ?", (start, end))
    total = float(s.energy_kwh.sum())
    return {
        "period": period, "start": start, "end": end,
        "total_kwh": round(total, 2), "predicted_kwh": round(float(s.predicted.sum()), 2),
        "estimated_cost_inr": round(total * COST_PER_KWH, 2), "alerts": int(s.is_alert.sum()),
        "saved_kwh": saved, "co2_kg": co2, "emission_factor": EMISSION_FACTOR, "cost_per_kwh": COST_PER_KWH,
        "highest_day": records(by_day.nlargest(1, "actual"))[0] if len(by_day) else None,
        "lowest_day": records(by_day.nsmallest(1, "actual"))[0] if len(by_day) else None,
        "by_day": records(by_day), "by_room": records(by_room),
    }


@app.get("/reports/{period}")
def report(period: str, _=Depends(current_user)):
    return build_report(period)


@app.get("/reports/{period}/csv")
def report_csv(period: str, _=Depends(current_user)):
    rep = build_report(period)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["date", "actual_kwh", "predicted_kwh", "alerts"])
    for r in rep["by_day"]:
        w.writerow([r["date"], r["actual"], r["predicted"], r["alerts"]])
    w.writerow([])
    w.writerow(["total_kwh", rep["total_kwh"], "energy_saved_kwh", rep["saved_kwh"],
                "co2_reduction_kg", rep["co2_kg"], "emission_factor", EMISSION_FACTOR])
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": f"attachment; filename={period}_report.csv"})


# ---------- model management (Step 17) ----------
@app.get("/model-info")
def model_info(_=Depends(current_user)):
    n = int(db.read_df("SELECT COUNT(*) AS n FROM readings").iloc[0, 0])
    return {**predictor.load()["metrics"], "total_readings": n}


@app.post("/retrain")
def retrain(_=Depends(current_user)):
    m = train_model.train()
    predictor.load(force=True)
    return m


@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...), _=Depends(current_user)):
    try:
        df = preprocess.clean(pd.read_csv(io.BytesIO(await file.read())))
    except Exception as e:
        raise HTTPException(422, f"Could not read CSV: {e}")
    if len(df) < 100:
        raise HTTPException(422, "CSV needs at least 100 valid rows.")
    db.load_readings(df, replace=True)
    m = train_model.train()
    predictor.load(force=True)
    return {"rows_loaded": len(df), "model": m}
# ---------- React frontend ----------
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend(full_path: str):
    index_file = FRONTEND_DIST / "index.html"

    if not index_file.exists():
        raise HTTPException(404, "Frontend build not found.")

    requested_file = (FRONTEND_DIST / full_path).resolve()

    if FRONTEND_DIST.resolve() in requested_file.parents and requested_file.is_file():
        return FileResponse(requested_file)

    return FileResponse(index_file)