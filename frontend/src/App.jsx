import { useState } from "react";
import { getToken, setToken } from "./api";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Analytics from "./pages/Analytics.jsx";
import Predict from "./pages/Predict.jsx";
import Alerts from "./pages/Alerts.jsx";
import Reports from "./pages/Reports.jsx";
import DataModel from "./pages/DataModel.jsx";

const TABS = [
  ["Dashboard", Dashboard], ["Analytics", Analytics], ["Prediction", Predict],
  ["Alerts", Alerts], ["Reports", Reports], ["Data & model", DataModel],
];

export default function App() {
  const [authed, setAuthed] = useState(!!getToken());
  const [tab, setTab] = useState("Dashboard");
  if (!authed) return <Login onLogin={() => setAuthed(true)} />;
  const Page = TABS.find(([n]) => n === tab)[1];
  return (
    <div className="shell">
      <aside className="side">
        <h1>Power IQ<br />AI Energy Saver</h1>
        <nav>
          {TABS.map(([name]) => (
            <button key={name} className={tab === name ? "active" : ""} onClick={() => setTab(name)}>{name}</button>
          ))}
        </nav>
        <button className="logout" onClick={() => { setToken(null); setAuthed(false); }}>Log out</button>
      </aside>
      <main><Page goTo={setTab} /></main>
    </div>
  );
}
