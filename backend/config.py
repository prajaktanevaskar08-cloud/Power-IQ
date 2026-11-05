import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "energy.db"
CSV_PATH = BASE_DIR / "data" / "energy_data.csv"
MODEL_PATH = BASE_DIR / "model.joblib"

# Model features (order matters)
FEATURES = ["hour", "day_of_week", "temperature", "occupancy", "room_code", "prev_energy"]

# Room metadata used by the data generator and the recommendation engine
ROOMS = {
    "Computer Lab 1": {"capacity": 50,  "base": 1.5, "per_person": 0.080},
    "Computer Lab 2": {"capacity": 40,  "base": 1.2, "per_person": 0.080},
    "Library":        {"capacity": 80,  "base": 2.0, "per_person": 0.030},
    "Classroom A101": {"capacity": 60,  "base": 0.8, "per_person": 0.020},
    "Seminar Hall":   {"capacity": 150, "base": 2.5, "per_person": 0.020},
}
DEFAULT_CAPACITY = 40

# Mention these values in your report: they are assumptions, not measurements.
EMISSION_FACTOR = 0.7     # kg CO2 per kWh (approx. Indian grid average)
COST_PER_KWH = 8.0        # INR per kWh (assumed tariff)

# Alert rule: actual must exceed the model's normal usage by 30% AND by 0.8 kWh
ALERT_RATIO = 1.3
ALERT_MIN_EXCESS = 0.8

SECRET_KEY = os.getenv("SECRET_KEY", "local-development-only-change-this")
TOKEN_HOURS = 12
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@pccoe.edu")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
