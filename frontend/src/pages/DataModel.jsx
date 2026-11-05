import { useEffect, useState } from "react";
import { api } from "../api";

export default function DataModel() {
  const [info, setInfo] = useState(null);
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState(false);
  const load = () => api.modelInfo().then(setInfo).catch((e) => setMsg(e.message));
  useEffect(() => { load(); }, []);

  async function run(fn, ok) {
    setBusy(true); setMsg("Working...");
    try { await fn(); setMsg(ok); await load(); } catch (e) { setMsg(e.message); }
    setBusy(false);
  }

  return (
    <>
      <header className="top"><h2>Data and model</h2></header>
      {info && (
        <section className="kpis">
          <div className="kpi"><span>Readings in database</span><b>{info.total_readings}</b></div>
          <div className="kpi"><span>Mean absolute error</span><b>{info.mae_kwh} kWh</b></div>
          <div className="kpi"><span>R² score</span><b>{info.r2}</b></div>
        </section>
      )}
      {info && (
        <section className="panel">
          <h3>What the model relies on</h3>
          {Object.entries(info.feature_importance).sort((a, b) => b[1] - a[1]).map(([k, v]) => (
            <div className="bar" key={k}><span>{k}</span><i style={{ width: `${v * 100}%` }} /><em>{(v * 100).toFixed(0)}%</em></div>
          ))}
        </section>
      )}
      <section className="panel">
        <h3>Upload a dataset</h3>
        <p className="muted">CSV columns: date, hour (or time), room, temperature, occupancy, energy_kwh. The model retrains after upload.</p>
        <input type="file" accept=".csv" disabled={busy} onChange={(e) => e.target.files[0] && run(() => api.upload(e.target.files[0]), "Dataset loaded and model retrained.")} />
        <p><button disabled={busy} onClick={() => run(api.retrain, "Model retrained on the latest data.")}>Retrain model</button></p>
        {msg && <p>{msg}</p>}
      </section>
    </>
  );
}
