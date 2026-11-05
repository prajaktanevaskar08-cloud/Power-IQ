"""Loads the saved model and scores readings (Steps 8, 10)."""
import joblib
import pandas as pd
import database as db
from config import FEATURES, MODEL_PATH, ALERT_RATIO, ALERT_MIN_EXCESS

_bundle = None


def load(force=False):
    global _bundle
    if _bundle is None or force:
        _bundle = joblib.load(MODEL_PATH)
        _bundle["model"].n_jobs = 1
    return _bundle


def _hist_means():
    df = db.read_df("SELECT room, hour, AVG(energy_kwh) AS m FROM readings GROUP BY room, hour")
    return {(r.room, int(r.hour)): float(r.m) for r in df.itertuples()}


def _predict(d: pd.DataFrame, prev=None):
    bundle = load()
    rooms = bundle["rooms"]
    d = d.copy()
    d["room_code"] = d["room"].map(lambda r: rooms.index(r) if r in rooms else -1)
    if prev is None:
        m = _hist_means()
        d["prev_energy"] = [m.get((r, h - 1), m.get((r, h), 0.0)) for r, h in zip(d["room"], d["hour"])]
    else:
        d["prev_energy"] = prev
    return bundle["model"].predict(d[FEATURES]).round(2)


def predict_one(room, hour, day_of_week, temperature, occupancy, prev_energy=None):
    d = pd.DataFrame([{"room": room, "hour": hour, "day_of_week": day_of_week,
                       "temperature": temperature, "occupancy": occupancy}])
    return float(_predict(d, prev_energy)[0])


def score(df: pd.DataFrame) -> pd.DataFrame:
    """Adds `predicted` (normal usage) and `is_alert` columns to readings."""
    d = df.copy()
    if d.empty:
        d["predicted"], d["is_alert"] = [], []
        return d
    d["day_of_week"] = pd.to_datetime(d["date"]).dt.dayofweek
    d["predicted"] = _predict(d)
    d["is_alert"] = (d["energy_kwh"] > d["predicted"] * ALERT_RATIO) & (d["energy_kwh"] - d["predicted"] >= ALERT_MIN_EXCESS)
    return d
