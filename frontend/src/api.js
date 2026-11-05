const BASE = import.meta.env.VITE_API_URL || "";
export const getToken = () => localStorage.getItem("token");
export const setToken = (t) => (t ? localStorage.setItem("token", t) : localStorage.removeItem("token"));

async function request(path, { method = "GET", body, form, raw } = {}) {
  const headers = {};
  if (getToken()) headers.Authorization = `Bearer ${getToken()}`;
  if (body) headers["Content-Type"] = "application/json";
  const res = await fetch(BASE + path, { method, headers, body: form || (body ? JSON.stringify(body) : undefined) });
  if (res.status === 401 && path !== "/login") {
    setToken(null);
    window.location.reload();
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const d = err.detail;
    throw new Error(Array.isArray(d) ? d.map((x) => `${x.loc.slice(1).join(".")}: ${x.msg}`).join("; ") : d || res.statusText);
  }
  return raw ? res : res.json();
}

export const api = {
  login: (email, password) => request("/login", { method: "POST", body: { email, password } }),
  rooms: () => request("/rooms"),
  status: () => request("/status"),
  summary: (room) => request(`/summary?room=${encodeURIComponent(room)}`),
  energy: (room) => request(`/energy-data?room=${encodeURIComponent(room)}`),
  analytics: (room) => request(`/analytics?room=${encodeURIComponent(room)}`),
  predict: (body) => request("/predict", { method: "POST", body }),
  alerts: () => request("/alerts"),
  action: (body) => request("/actions", { method: "POST", body }),
  spike: (room) => request("/simulate-spike", { method: "POST", body: { room } }),
  report: (p) => request(`/reports/${p}`),
  reportCsv: async (p) => {
    const blob = await (await request(`/reports/${p}/csv`, { raw: true })).blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${p}_report.csv`;
    a.click();
  },
  modelInfo: () => request("/model-info"),
  retrain: () => request("/retrain", { method: "POST" }),
  upload: (file) => {
    const f = new FormData();
    f.append("file", file);
    return request("/upload-csv", { method: "POST", form: f });
  },
};

export const fmtHour = (h) => `${h % 12 || 12}${h < 12 ? " AM" : " PM"}`;
