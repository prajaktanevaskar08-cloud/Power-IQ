import { useEffect, useState } from "react";
import { api, fmtHour } from "../api";

function AlertCard({ a, onSaved }) {
  const [after, setAfter] = useState("");
  const [error, setError] = useState("");

  async function save() {
    try {
      await api.action({ room: a.room, date: a.date, hour: a.hour, before_kwh: a.current_kwh, after_kwh: +after });
      onSaved();
    } catch (e) { setError(e.message); }
  }

  return (
    <div className={`card alert ${a.severity} ${a.action ? "done" : ""}`}>
      <h4>⚠️ {a.message}</h4>
      <p className="muted">{a.date} · {fmtHour(a.hour)} · {a.occupancy} people · {a.devices_on} devices on</p>
      <p>Current <b>{a.current_kwh} kWh</b> vs normal <b>{a.normal_kwh} kWh</b></p>
      <ul>{a.recommendations.map((r) => <li key={r}>{r}</li>)}</ul>
      {a.action ? (
        <p className="saved">Action recorded: usage dropped to {a.action.after_kwh} kWh. Saved {a.action.saved_kwh} kWh ({a.action.co2_kg} kg CO₂).</p>
      ) : (
        <div className="inline">
          <input type="number" step="0.1" placeholder="Usage after action (kWh)" value={after} onChange={(e) => setAfter(e.target.value)} />
          <button className="primary" disabled={after === ""} onClick={save}>Record action taken</button>
        </div>
      )}
      {error && <p className="error">{error}</p>}
    </div>
  );
}

export default function Alerts() {
  const [data, setData] = useState(null);
  const [rooms, setRooms] = useState([]);
  const [room, setRoom] = useState("");
  const [error, setError] = useState("");
  const load = () => api.alerts().then(setData).catch((e) => setError(e.message));

  useEffect(() => { load(); api.rooms().then((r) => { setRooms(r); setRoom(r[0]?.name || ""); }); }, []);

  async function spike() {
    try { await api.spike(room); await load(); } catch (e) { setError(e.message); }
  }

  return (
    <>
      <header className="top">
        <h2>Alerts and recommendations</h2>
        <div className="inline">
          <select value={room} onChange={(e) => setRoom(e.target.value)}>{rooms.map((r) => <option key={r.name}>{r.name}</option>)}</select>
          <button onClick={spike}>Simulate high usage</button>
        </div>
      </header>
      {error && <p className="error">{error}</p>}
      {data && <p className="muted">Readings for {data.date}. {data.alerts.length} alert(s).</p>}
      <section className="cards">
        {data?.alerts.map((a) => <AlertCard key={`${a.room}-${a.hour}`} a={a} onSaved={load} />)}
        {data && data.alerts.length === 0 && <p>No unusual usage detected. Use “Simulate high usage” to test an alert.</p>}
      </section>
    </>
  );
}
