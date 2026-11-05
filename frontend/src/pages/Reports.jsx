import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api";

export default function Reports() {
  const [period, setPeriod] = useState("weekly");
  const [r, setR] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { api.report(period).then(setR).catch((e) => setError(e.message)); }, [period]);

  return (
    <>
      <header className="top">
        <h2>Reports</h2>
        <div className="inline">
          <select value={period} onChange={(e) => setPeriod(e.target.value)}>
            <option value="daily">Daily</option><option value="weekly">Weekly</option><option value="monthly">Monthly</option>
          </select>
          <button onClick={() => api.reportCsv(period)}>Download CSV</button>
        </div>
      </header>
      {error && <p className="error">{error}</p>}
      {r && (
        <>
          <p className="muted">{r.start} to {r.end}</p>
          <section className="kpis">
            <div className="kpi"><span>Total consumed</span><b>{r.total_kwh} kWh</b></div>
            <div className="kpi"><span>Predicted</span><b>{r.predicted_kwh} kWh</b></div>
            <div className="kpi"><span>Estimated cost</span><b>₹{r.estimated_cost_inr}</b></div>
            <div className="kpi warn"><span>High-usage alerts</span><b>{r.alerts}</b></div>
            <div className="kpi good"><span>Energy saved</span><b>{r.saved_kwh} kWh</b></div>
            <div className="kpi good"><span>Carbon reduction</span><b>{r.co2_kg} kg CO₂</b></div>
          </section>
          <p className="muted">Assumptions: {r.emission_factor} kg CO₂ per kWh, ₹{r.cost_per_kwh} per kWh.</p>
          {r.highest_day && <p>Highest day: <b>{r.highest_day.date}</b> ({r.highest_day.actual} kWh). Lowest day: <b>{r.lowest_day.date}</b> ({r.lowest_day.actual} kWh).</p>}
          <section className="panel">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={r.by_day}>
                <CartesianGrid strokeDasharray="3 3" stroke="#d9e0e4" /><XAxis dataKey="date" /><YAxis unit=" kWh" width={70} /><Tooltip /><Legend />
                <Bar dataKey="actual" name="Actual" fill="#0f6b5c" /><Bar dataKey="predicted" name="Predicted" fill="#d98a1c" />
              </BarChart>
            </ResponsiveContainer>
          </section>
          <table>
            <thead><tr><th>Room</th><th>Actual kWh</th><th>Predicted kWh</th><th>Alerts</th></tr></thead>
            <tbody>{r.by_room.map((x) => <tr key={x.room}><td>{x.room}</td><td>{x.actual}</td><td>{x.predicted}</td><td>{x.alerts}</td></tr>)}</tbody>
          </table>
        </>
      )}
    </>
  );
}
