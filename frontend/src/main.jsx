import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import "./styles.css";

// Shows the real error on screen instead of a blank page.
class ErrorBoundary extends React.Component {
  state = { error: null };
  static getDerivedStateFromError(error) { return { error }; }
  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div style={{ padding: 24, fontFamily: "monospace" }}>
        <h2>Something crashed</h2>
        <pre style={{ whiteSpace: "pre-wrap", color: "#b8402f" }}>{String(this.state.error?.stack || this.state.error)}</pre>
        <button onClick={() => { localStorage.clear(); location.reload(); }}>Clear saved login and reload</button>
      </div>
    );
  }
}

createRoot(document.getElementById("root")).render(<ErrorBoundary><App /></ErrorBoundary>);
