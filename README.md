# Power IQ 

React dashboard + FastAPI backend + Random Forest model that predicts room-level electricity use,
flags unusual consumption, recommends actions, and reports energy saved and CO2 reduction.

## Run the backend (Python 3.10+)
```bash
cd backend
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload                            # http://localhost:8000/docs
```
First start creates `data/energy_data.csv` (dummy data), loads it into SQLite, and trains `model.joblib`.
Login: `admin@pccoe.edu` / `admin123` (change in `config.py`).

## Run the frontend (Node 18+)
```bash
cd frontend
npm install
npm run dev                                          # http://localhost:5173
```

## Demo flow
1. Log in, show the dashboard (actual vs predicted).
2. Prediction page: Computer Lab 1, 2 PM, 30 C, 20 people.
3. Alerts page: click "Simulate high usage", show the alert and recommendation.
4. Enter the usage after action (e.g. 4.2) and record it: energy saved and CO2 appear.
5. Reports page: weekly report and CSV download. Data and model page: upload CSV, retrain.

## Be upfront in your report
- Data is simulated. Energy = base load + people x per-person load + AC load + noise, with about 3% injected anomalies.
- Emission factor (0.7 kg CO2/kWh) and tariff (Rs 8/kWh) are assumptions in `config.py`.
- "Normal usage" is the model's prediction for that room, hour, temperature and occupancy.
- The model uses the previous hour's usage; for alerts and /predict it uses the room's historical average for that hour.
- Energy saved comes from the admin's recorded before/after readings. Without IoT it is manual.
