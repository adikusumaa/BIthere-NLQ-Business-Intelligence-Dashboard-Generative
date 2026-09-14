import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuthStore } from "../store/authStore";

const styles = {
  page: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "100vh",
    padding: "24px",
  },
  card: {
    width: "100%",
    maxWidth: "400px",
    background: "var(--color-bg-soft)",
    border: "1px solid var(--color-border)",
    borderRadius: "8px",
    padding: "32px",
  },
  title: {
    fontSize: "24px",
    fontWeight: "700",
    marginBottom: "4px",
  },
  subtitle: {
    fontSize: "13px",
    color: "var(--color-text-dim)",
    marginBottom: "24px",
  },
  label: {
    display: "block",
    fontSize: "12px",
    fontWeight: "600",
    color: "var(--color-text-dim)",
    marginBottom: "6px",
    textTransform: "uppercase",
    letterSpacing: "0.04em",
  },
  input: {
    width: "100%",
    padding: "10px 12px",
    background: "var(--color-bg)",
    border: "1px solid var(--color-border)",
    borderRadius: "6px",
    color: "var(--color-text)",
    marginBottom: "16px",
  },
  button: {
    width: "100%",
    padding: "10px 12px",
    background: "var(--color-accent)",
    color: "#ffffff",
    borderRadius: "6px",
    fontSize: "14px",
    fontWeight: "600",
    transition: "background 0.15s",
  },
  error: {
    background: "rgba(248, 81, 73, 0.1)",
    border: "1px solid var(--color-danger)",
    color: "var(--color-danger)",
    padding: "10px 12px",
    borderRadius: "6px",
    fontSize: "13px",
    marginBottom: "16px",
  },
};

export default function Login() {
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
      navigate("/chat");
    } catch (err) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <div style={styles.title}>BIthere</div>
        <div style={styles.subtitle}>AI Business Intelligence Analyst</div>

        {error && <div style={styles.error}>{error}</div>}

        <form onSubmit={handleSubmit}>
          <label style={styles.label}>Email</label>
          <input
            style={styles.input}
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
            autoFocus
          />

          <label style={styles.label}>Password</label>
          <input
            style={styles.input}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Your password"
            required
          />

          <button
            type="submit"
            style={styles.button}
            disabled={loading}
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}