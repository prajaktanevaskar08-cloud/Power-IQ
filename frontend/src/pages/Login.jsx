import { useState } from "react";
import { api, setToken } from "../api";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("admin@pccoe.edu");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState("");

  async function submit(e) {
    e.preventDefault();
    try {
      const r = await api.login(email, password);
      setToken(r.token);
      onLogin();
    } catch (err) { setError(err.message); }
  }

  return (
    <div className="login">
      <form onSubmit={submit} className="panel">
        <h1>Campus Energy AI</h1>
        <p className="muted">Log in to see usage, predictions and alerts.</p>
        <label>Email<input value={email} onChange={(e) => setEmail(e.target.value)} /></label>
        <label>Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} /></label>
        {error && <p className="error">{error}</p>}
        <button className="primary">Log in</button>
      </form>
    </div>
  );
}
