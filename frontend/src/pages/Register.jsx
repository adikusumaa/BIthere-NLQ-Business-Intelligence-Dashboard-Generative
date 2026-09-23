import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

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
  success: {
    background: "rgba(52, 199, 89, 0.08)",
    color: "var(--ios-green)",
    padding: "12px 14px",
    borderRadius: "var(--radius-md)",
    fontSize: "14px",
    marginBottom: "16px",
    border: "1px solid rgba(52, 199, 89, 0.2)",
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
  loginLink: {
    display: "block",
    marginTop: "16px",
    textAlign: "center",
    fontSize: "14px",
    color: "var(--ios-blue)",
    textDecoration: "none",
  },
};

export default function Register() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || `HTTP ${response.status}`);
      }
      setSuccess("Account created. Redirecting to login...");
      setTimeout(() => navigate("/login"), 1500);
    } catch (err) {
      setError(err.message);
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
          <div style={styles.brand}>Create Account</div>
          <div style={styles.tagline}>
            Use the email your administrator invited
          </div>
        </div>

        {error && <div style={styles.error}>{error}</div>}
        {success && <div style={styles.success}>{success}</div>}

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
              placeholder="At least 6 characters"
              required
              minLength={6}
              autoComplete="new-password"
            />
          </div>

          <div style={styles.fieldGroup}>
            <label style={styles.label}>CONFIRM PASSWORD</label>
            <input
              className="ios-input"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Repeat password"
              required
              autoComplete="new-password"
            />
          </div>

          <button
            type="submit"
            style={styles.submit}
            disabled={loading}
            className="ios-btn"
          >
            {loading ? "Creating account..." : "Create Account"}
          </button>
        </form>

        <Link to="/login" style={styles.loginLink}>
          Already have an account? Sign in
        </Link>

        <div style={styles.footer}>
          Registration is invite-only. Contact your administrator.
        </div>
      </div>
    </div>
  );
}