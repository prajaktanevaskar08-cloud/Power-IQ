"""Step 3 - data cleaning. Accepts our CSV format or the one from the problem statement."""
import pandas as pd

RENAMES = {
    "building/room": "room", "building": "room",
    "energy_consumption": "energy_kwh", "actual_energy_consumption": "energy_kwh", "energy": "energy_kwh",
    "temp": "temperature", "number_of_people": "occupancy", "people": "occupancy",
    "device_usage": "devices_on",
}
REQUIRED = ["date", "hour", "room", "temperature", "occupancy", "energy_kwh"]
OUT_COLS = ["date", "hour", "room", "temperature", "occupancy", "devices_on", "energy_kwh", "prev_energy"]


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = df.rename(columns={k: v for k, v in RENAMES.items() if k in df.columns})

    if "hour" not in df.columns and "time" in df.columns:        # "10:00 AM" -> 10
        df["hour"] = pd.to_datetime(df["time"].astype(str), errors="coerce").dt.hour
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing columns: {missing}")

    raw = df["date"].astype(str).str.strip()
    parsed = pd.to_datetime(raw, errors="coerce", format="ISO8601")      # 2026-09-07
    parsed = parsed.fillna(pd.to_datetime(raw, errors="coerce", dayfirst=True, format="mixed"))  # 07-09-2026
    df["date"] = parsed
    for col in ["hour", "temperature", "occupancy", "energy_kwh"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["room"] = df["room"].astype(str).str.strip()

    df = df.dropna(subset=REQUIRED)                                # remove missing values
    df = df[(df.energy_kwh >= 0) & (df.occupancy >= 0) & df.hour.between(0, 23)]  # remove wrong values
    df["hour"] = df["hour"].astype(int)
    df["occupancy"] = df["occupancy"].astype(int)
    if "devices_on" not in df.columns:
        df["devices_on"] = df["occupancy"]
    df["devices_on"] = pd.to_numeric(df["devices_on"], errors="coerce").fillna(df["occupancy"]).astype(int)

    df = df.sort_values(["date", "hour"]).drop_duplicates(["date", "hour", "room"], keep="last")
    if "prev_energy" not in df.columns:
        df["prev_energy"] = df.groupby("room")["energy_kwh"].shift(1)
    df["prev_energy"] = pd.to_numeric(df["prev_energy"], errors="coerce").fillna(df["energy_kwh"])
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    return df[OUT_COLS].reset_index(drop=True)
