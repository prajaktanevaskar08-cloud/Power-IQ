"""Step 5 - Random Forest training. Run: python train_model.py"""
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
import database as db
from config import FEATURES, MODEL_PATH


def train():
    df = db.read_df("SELECT * FROM readings")
    if len(df) < 100:
        raise ValueError("Need at least 100 readings to train the model.")
    rooms = sorted(df["room"].unique().tolist())
    df["day_of_week"] = pd.to_datetime(df["date"]).dt.dayofweek
    df["room_code"] = df["room"].map(rooms.index)

    X, y = df[FEATURES], df["energy_kwh"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=200, max_depth=14, min_samples_leaf=3, random_state=42, n_jobs=-1)
    model.fit(X_tr, y_tr)
    pred = model.predict(X_te)

    metrics = {
        "mae_kwh": round(float(mean_absolute_error(y_te, pred)), 3),
        "r2": round(float(r2_score(y_te, pred)), 3),
        "train_rows": int(len(X_tr)),
        "test_rows": int(len(X_te)),
        "feature_importance": {f: round(float(v), 3) for f, v in zip(FEATURES, model.feature_importances_)},
    }
    joblib.dump({"model": model, "rooms": rooms, "metrics": metrics}, MODEL_PATH)
    return metrics


if __name__ == "__main__":
    import database
    database.init_db()
    print(train())
