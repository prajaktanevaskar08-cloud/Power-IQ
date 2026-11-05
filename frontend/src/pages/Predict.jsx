import { useEffect, useState } from "react";
import { api } from "../api";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export default function Predict() {
  const [rooms, setRooms] = useState([]);
  const [f, setF] = useState({ room: "", hour: 14, day: 1, temperature: 30, occupancy: 20 });
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => { api.rooms().then((r) => { setRooms(r); setF((p) => ({ ...p, room: r[0]?.name || "" })); }); }, []);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  async function run() {
    setError(""); setResult(null);
    try {
      setResult(await api.predict({ room: f.room, hour: +f.hour, day: +f.day, temperature: +f.temperature, occupancy: +f.occupancy }));
    } catch (e) { setError(e.message); }
  }

  return (
    <>
      <header className="top"><h2>Predict energy usage</h2></header>
      <section className="panel form">
        <label>Room<select value={f.room} onChange={set("room")}>{rooms.map((r) => <option key={r.name}>{r.name}</option>)}</select></label>
        <label>Day<select value={f.day} onChange={set("day")}>{DAYS.map((d, i) => <option key={d} value={i}>{d}</option>)}</select></label>
        <label>Hour (0-23)<input type="number" value={f.hour} onChange={set("hour")} /></label>
        <label>Temperature (°C)<input type="number" value={f.temperature} onChange={set("temperature")} /></label>
        <label>People in room<input type="number" value={f.occupancy} onChange={set("occupancy")} /></label>
        <button className="primary" onClick={run}>Predict energy usage</button>
      </section>
      {error && <p className="error">{error}</p>}
      {result && (
        <section className="kpis">
          <div className="kpi"><span>Expected usage</span><b>{result.predicted_kwh} kWh</b></div>
          <div className="kpi"><span>Estimated cost</span><b>₹{result.estimated_cost_inr}</b></div>
          <div className="kpi"><span>Estimated emissions</span><b>{result.estimated_co2_kg} kg CO₂</b></div>
        </section>
      )}
    </>
  );
}
