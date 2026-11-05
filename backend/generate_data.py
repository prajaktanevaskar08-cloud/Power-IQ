"""Creates a realistic dummy dataset (Step 2). Run: python generate_data.py"""
from datetime import date, timedelta
import numpy as np
import pandas as pd
from config import ROOMS, CSV_PATH

PROFILE = {8: .30, 9: .80, 10: .90, 11: .85, 12: .40, 13: .60, 14: .80, 15: .75, 16: .50, 17: .20}


def generate(path=CSV_PATH, days=120, seed=42):
    rng = np.random.default_rng(seed)
    end = date.today() - timedelta(days=1)
    rows = []
    for d in (end - timedelta(days=i) for i in range(days - 1, -1, -1)):
        dow = d.weekday()
        day_factor = 0.0 if dow == 6 else 0.3 if dow == 5 else 1.0
        day_temp = rng.normal(0, 1.5)
        for room, cfg in ROOMS.items():
            for hour in range(8, 18):
                occ = int(np.clip(cfg["capacity"] * PROFILE[hour] * day_factor * rng.uniform(0.7, 1.05), 0, cfg["capacity"]))
                temp = round(25 + 6 * np.sin((hour - 8) / 10 * np.pi) + day_temp + rng.normal(0, 0.7), 1)
                if occ == 0:
                    energy = cfg["base"] * 0.25                      # standby load only
                else:
                    energy = cfg["base"] + occ * cfg["per_person"] + max(0, temp - 24) * 0.15
                energy += rng.normal(0, 0.12)
                devices = occ + int(rng.integers(0, 4)) if occ else 0
                if rng.random() < 0.03:                              # devices left on -> anomaly
                    energy += rng.uniform(2, 4)
                    devices = int(cfg["capacity"] * 0.8)
                rows.append([d.isoformat(), hour, room, temp, occ, devices, round(max(energy, 0.1), 2)])
    df = pd.DataFrame(rows, columns=["date", "hour", "room", "temperature", "occupancy", "devices_on", "energy_kwh"])
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return df


if __name__ == "__main__":
    print(f"Wrote {len(generate())} rows to {CSV_PATH}")
