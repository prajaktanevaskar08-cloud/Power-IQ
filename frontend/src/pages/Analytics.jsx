import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from "recharts";
import { api, fmtHour } from "../api";

export default function Analytics() {
  const [rooms, setRooms] = useState([]);
  const [room, setRoom] = useState("");
  const [data, setData] = useState(null);

  useEffect(() => { api.rooms().then((r) => { setRooms(r); setRoom(r[0]?.name || ""); }); }, []);
  useEffect(() => { if (room) api.analytics(room).then(setData); }, [room]);

  return (
    <>
      <header className="top">
        <h2>Analytics</h2>
        <select value={room} onChange={(e) => setRoom(e.target.value)}>{rooms.map((r) => <option key={r.name}>{r.name}</option>)}</select>
      </header>
      {data && (
        <div className="grid2">
          <section className="panel"><h3>Average usage by hour</h3>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data.hourly.map((h) => ({ ...h, label: fmtHour(h.hour) }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="#d9e0e4" /><XAxis dataKey="label" /><YAxis unit=" kWh" width={70} /><Tooltip />
                <Bar dataKey="energy" name="Avg kWh" fill="#0f6b5c" />
              </BarChart>
            </ResponsiveContainer>
          </section>
          <section className="panel"><h3>Average usage by weekday</h3>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data.weekday}>
                <CartesianGrid strokeDasharray="3 3" stroke="#d9e0e4" /><XAxis dataKey="day" /><YAxis unit=" kWh" width={70} /><Tooltip />
                <Bar dataKey="energy" name="Avg kWh" fill="#d98a1c" />
              </BarChart>
            </ResponsiveContainer>
          </section>
          <section className="panel wide"><h3>Occupancy vs energy</h3>
            <ResponsiveContainer width="100%" height={280}>
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#d9e0e4" />
                <XAxis dataKey="occupancy" name="People" type="number" /><YAxis dataKey="energy_kwh" name="kWh" type="number" width={50} />
                <Tooltip cursor={{ strokeDasharray: "3 3" }} /><Scatter data={data.scatter} fill="#0f6b5c" />
              </ScatterChart>
            </ResponsiveContainer>
          </section>
        </div>
      )}
    </>
  );
}
