import { useEffect, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Legend } from "recharts";
import { api, fmtHour } from "../api";

export default function Dashboard() {
  const [rooms, setRooms] = useState([]);
  const [room, setRoom] = useState("");
  const [summary, setSummary] = useState(null);
  const [rows, setRows] = useState([]);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.rooms().then((r) => { setRooms(r); setRoom(r[0]?.name || ""); }).catch((e) => setError(e.message));
    api.status().then(setStatus).catch((e) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!room) return;
    api.summary(room).then(setSummary).catch((e) => setError(e.message));
    api.energy(room).then((d) => setRows(d.rows.map((r) => ({ ...r, label: fmtHour(r.hour) })))).catch((e) => setError(e.message));
  }, [room]);

  return (
    <>
      <header className="top">
        <h2>Dashboard</h2>
        <select value={room} onChange={(e) => setRoom(e.target.value)}>
          {rooms.map((r) => <option key={r.name}>{r.name}</option>)}
        </select>
      </header>
      {error && <p className="error">{error}</p>}
      {summary && (
        <section className="kpis">
          <div className="kpi"><span>Used on {summary.date}</span><b>{summary.actual_kwh} kWh</b></div>
          <div className="kpi"><span>Expected for the day</span><b>{summary.predicted_kwh} kWh</b></div>
          <div className="kpi warn"><span>High-usage alerts</span><b>{summary.alerts}</b></div>
          <div className="kpi good"><span>Energy saved (all rooms)</span><b>{summary.saved_kwh} kWh</b></div>
          <div className="kpi good"><span>Carbon reduction</span><b>{summary.co2_kg} kg CO₂</b></div>
        </section>
      )}
      <section className="panel">
        <h3>Actual vs predicted usage</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" stroke="#d9e0e4" />
            <XAxis dataKey="label" /><YAxis unit=" kWh" width={70} /><Tooltip /><Legend />
            <Line type="monotone" dataKey="energy_kwh" name="Actual" stroke="#0f6b5c" strokeWidth={2.5} />
            <Line type="monotone" dataKey="predicted" name="Predicted" stroke="#d98a1c" strokeDasharray="6 4" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </section>
      <h3>Room status (latest reading)</h3>
      <section className="cards">
        {status?.rooms.map((r) => (
          <div key={r.room} className={`card ${r.status === "Normal" ? "" : "high"}`}>
            <h4>{r.room}</h4>
            <p className="muted">{fmtHour(r.hour)} · {r.occupancy}/{r.capacity} people</p>
            <p>Current usage: <b>{r.current_kwh} kWh</b></p>
            <p>Normal usage: <b>{r.normal_kwh} kWh</b></p>
            <p className="status">{r.status}</p>
            {r.recommendations[0] && <p className="rec">{r.recommendations[0]}</p>}
          </div>
        ))}
      </section>
    </>
  );
}
