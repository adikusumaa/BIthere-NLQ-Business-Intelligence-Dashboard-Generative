import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuthStore } from "../store/authStore";

const styles = {
  page: {
    minHeight: "100vh",
    background: "var(--ios-bg)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "24px",
  },
  card: {
    width: "100%",
    maxWidth: "420px",
    background: "var(--ios-surface)",
    borderRadius: "var(--radius-xl)",
    boxShadow: "var(--shadow-lg)",
    padding: "40px 32px 32px 32px",
    border: "1px solid var(--ios-separator)",
  },
  logoWrap: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    marginBottom: "32px",
  },
  logoMark: {
    width: "64px",
    height: "64px",
    borderRadius: "18px",
    background: "linear-gradient(135deg, #007AFF 0%, #5856D6 100%)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    boxShadow: "0 8px 24px rgba(0, 122, 255, 0.28)",
    marginBottom: "16px",
  },
  logoLetter: {
    color: "#FFFFFF",
    fontSize: "32px",
    fontWeight: "700",
    letterSpacing: "-0.02em",
  },
  brand: {
    fontSize: "26px",
    fontWeight: "700",
    letterSpacing: "-0.02em",
    color: "var(--ios-text)",
    marginBottom: "4px",
  },
  tagline: {
    fontSize: "14px",
    color: "var(--ios-text-secondary)",
    textAlign: "center",
  },
  label: {
    display: "block",
    fontSize: "13px",
    fontWeight: "600",
    color: "var(--ios-text-secondary)",
    marginBottom: "8px",
    letterSpacing: "0.02em",
  },
  fieldGroup: {
    marginBottom: "16px",
  },
  error: {
    background: "rgba(255, 59, 48, 0.08)",
    color: "var(--ios-red)",
    padding: "12px 14px",
    borderRadius: "var(--radius-md)",
    fontSize: "14px",
    marginBottom: "16px",
    border: "1px solid rgba(255, 59, 48, 0.2)",
  },
  submit: {
    width: "100%",
    padding: "16px",
    marginTop: "8px",
    fontSize: "17px",
    fontWeight: "600",
    background: "var(--ios-blue)",
    color: "#FFFFFF",
    borderRadius: "var(--radius-md)",
  },
  footer: {
    marginTop: "24px",
    textAlign: "center",
    fontSize: "12px",
    color: "var(--ios-text-tertiary)",
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
      setError(err.message || "Sign in failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <div style={styles.logoWrap}>
          <div style={styles.logoMark}>
            <span style={styles.logoLetter}>B</span>
          </div>
          <div style={styles.brand}>BIthere</div>
          <div style={styles.tagline}>AI Business Intelligence Analyst</div>
        </div>

        {error && <div style={styles.error}>{error}</div>}

        <form onSubmit={handleSubmit}>
          <div style={styles.fieldGroup}>
            <label style={styles.label}>EMAIL</label>
            <input
              className="ios-input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              autoFocus
              autoComplete="email"
            />
          </div>

          <div style={styles.fieldGroup}>
            <label style={styles.label}>PASSWORD</label>
            <input
              className="ios-input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Your password"
              required
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            style={styles.submit}
            disabled={loading}
            className="ios-btn"
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <div style={styles.footer}>
          Internal use only. Contact your administrator for access.
        </div>
      </div>
    </div>
  );
}