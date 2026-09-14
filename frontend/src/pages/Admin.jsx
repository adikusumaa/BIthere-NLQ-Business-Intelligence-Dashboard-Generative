import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuthStore } from "../store/authStore";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const styles = {
  page: {
    minHeight: "100vh",
    background: "var(--color-bg)",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "12px 20px",
    borderBottom: "1px solid var(--color-border)",
    background: "var(--color-bg-soft)",
  },
  brand: { display: "flex", alignItems: "center", gap: "10px" },
  brandName: { fontSize: "16px", fontWeight: "700" },
  brandTag: { fontSize: "11px", color: "var(--color-text-dim)" },
  actions: { display: "flex", gap: "12px", alignItems: "center" },
  userEmail: { fontSize: "12px", color: "var(--color-text-dim)" },
  btn: {
    padding: "6px 12px",
    background: "transparent",
    color: "var(--color-text-dim)",
    border: "1px solid var(--color-border)",
    borderRadius: "6px",
    fontSize: "12px",
    textDecoration: "none",
  },
  btnPrimary: {
    padding: "8px 16px",
    background: "var(--color-accent)",
    color: "#ffffff",
    border: "none",
    borderRadius: "6px",
    fontSize: "13px",
    fontWeight: "600",
  },
  container: { padding: "32px 40px", maxWidth: "1100px", margin: "0 auto" },
  title: { fontSize: "22px", fontWeight: "700", marginBottom: "4px" },
  subtitle: {
    fontSize: "13px",
    color: "var(--color-text-dim)",
    marginBottom: "24px",
  },
  toolbar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "16px",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
    background: "var(--color-bg-soft)",
    borderRadius: "8px",
    overflow: "hidden",
    border: "1px solid var(--color-border)",
  },
  th: {
    textAlign: "left",
    padding: "10px 16px",
    background: "var(--color-bg)",
    color: "var(--color-text-dim)",
    fontSize: "11px",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    borderBottom: "1px solid var(--color-border)",
  },
  td: {
    padding: "12px 16px",
    fontSize: "13px",
    borderBottom: "1px solid var(--color-border)",
  },
  roleBadge: (role) => ({
    display: "inline-block",
    padding: "2px 10px",
    borderRadius: "12px",
    fontSize: "11px",
    fontWeight: "600",
    background:
      role === "admin"
        ? "rgba(31, 111, 235, 0.15)"
        : "rgba(139, 148, 158, 0.15)",
    color: role === "admin" ? "#58a6ff" : "var(--color-text-dim)",
  }),
  actionBtn: {
    padding: "4px 10px",
    background: "transparent",
    color: "var(--color-text-dim)",
    border: "1px solid var(--color-border)",
    borderRadius: "4px",
    fontSize: "12px",
    marginRight: "6px",
  },
  actionBtnDanger: {
    padding: "4px 10px",
    background: "transparent",
    color: "var(--color-danger)",
    border: "1px solid var(--color-danger)",
    borderRadius: "4px",
    fontSize: "12px",
  },
  modal: {
    position: "fixed",
    inset: 0,
    background: "rgba(0, 0, 0, 0.7)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 1000,
  },
  modalCard: {
    width: "100%",
    maxWidth: "440px",
    background: "var(--color-bg-soft)",
    border: "1px solid var(--color-border)",
    borderRadius: "8px",
    padding: "24px",
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
    marginBottom: "14px",
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
  success: {
    background: "rgba(63, 185, 80, 0.1)",
    border: "1px solid var(--color-success)",
    color: "var(--color-success)",
    padding: "10px 12px",
    borderRadius: "6px",
    fontSize: "13px",
    marginBottom: "16px",
  },
};

export default function Admin() {
  const navigate = useNavigate();
  const role = useAuthStore((s) => s.role);
  const user = useAuthStore((s) => s.user);
  const getToken = useAuthStore((s) => s.getToken);
  const logout = useAuthStore((s) => s.logout);

  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [showInvite, setShowInvite] = useState(false);
  const [inviteForm, setInviteForm] = useState({
    email: "",
    role: "analyst",
    password: "",
  });

  useEffect(() => {
    if (role && role !== "admin") {
      navigate("/chat");
    }
  }, [role, navigate]);

  const loadUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/users`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setUsers(await response.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleInvite = async (event) => {
    event.preventDefault();
    setError(null);
    setSuccess(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/users`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify(inviteForm),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || `HTTP ${response.status}`);
      }
      setSuccess(`User ${data.email} berhasil dibuat`);
      setShowInvite(false);
      setInviteForm({ email: "", role: "analyst", password: "" });
      loadUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRoleChange = async (userId, newRole) => {
    setError(null);
    setSuccess(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/users/${userId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify({ role: newRole }),
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || `HTTP ${response.status}`);
      }
      setSuccess(`Role diubah ke ${newRole}`);
      loadUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (userId, email) => {
    if (!window.confirm(`Hapus user ${email}?`)) return;
    setError(null);
    setSuccess(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/users/${userId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || `HTTP ${response.status}`);
      }
      setSuccess(`User ${email} dihapus`);
      loadUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <div style={styles.brand}>
          <div style={styles.brandName}>BIthere</div>
          <div style={styles.brandTag}>Admin Panel</div>
        </div>
        <div style={styles.actions}>
          <span style={styles.userEmail}>{user?.email}</span>
          <Link to="/chat" style={styles.btn}>
            Ke Chat
          </Link>
          <button style={styles.btn} onClick={handleLogout}>
            Logout
          </button>
        </div>
      </header>

      <div style={styles.container}>
        <h1 style={styles.title}>User Management</h1>
        <div style={styles.subtitle}>
          Kelola user, role, dan akses ke platform BIthere.
        </div>

        {error && <div style={styles.error}>{error}</div>}
        {success && <div style={styles.success}>{success}</div>}

        <div style={styles.toolbar}>
          <div style={{ fontSize: "13px", color: "var(--color-text-dim)" }}>
            {loading ? "Loading..." : `${users.length} user`}
          </div>
          <button
            style={styles.btnPrimary}
            onClick={() => setShowInvite(true)}
          >
            + Invite User
          </button>
        </div>

        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>Email</th>
              <th style={styles.th}>Role</th>
              <th style={styles.th}>Created</th>
              <th style={styles.th}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td style={styles.td}>{u.email}</td>
                <td style={styles.td}>
                  <span style={styles.roleBadge(u.role)}>{u.role}</span>
                </td>
                <td style={{ ...styles.td, color: "var(--color-text-dim)" }}>
                  {u.created_at
                    ? new Date(u.created_at).toLocaleDateString("id-ID")
                    : "-"}
                </td>
                <td style={styles.td}>
                  <button
                    style={styles.actionBtn}
                    onClick={() =>
                      handleRoleChange(
                        u.id,
                        u.role === "admin" ? "analyst" : "admin"
                      )
                    }
                    disabled={u.id === user?.id}
                  >
                    {u.role === "admin" ? "Demote" : "Promote"}
                  </button>
                  <button
                    style={styles.actionBtnDanger}
                    onClick={() => handleDelete(u.id, u.email)}
                    disabled={u.id === user?.id}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showInvite && (
        <div style={styles.modal} onClick={() => setShowInvite(false)}>
          <div
            style={styles.modalCard}
            onClick={(e) => e.stopPropagation()}
          >
            <h2
              style={{ fontSize: "16px", fontWeight: "700", marginBottom: "16px" }}
            >
              Invite User
            </h2>
            <form onSubmit={handleInvite}>
              <label style={styles.label}>Email</label>
              <input
                style={styles.input}
                type="email"
                value={inviteForm.email}
                onChange={(e) =>
                  setInviteForm((s) => ({ ...s, email: e.target.value }))
                }
                required
                autoFocus
              />

              <label style={styles.label}>Temporary Password</label>
              <input
                style={styles.input}
                type="text"
                value={inviteForm.password}
                onChange={(e) =>
                  setInviteForm((s) => ({ ...s, password: e.target.value }))
                }
                minLength={6}
                required
              />

              <label style={styles.label}>Role</label>
              <select
                style={styles.input}
                value={inviteForm.role}
                onChange={(e) =>
                  setInviteForm((s) => ({ ...s, role: e.target.value }))
                }
              >
                <option value="analyst">Analyst</option>
                <option value="admin">Admin</option>
              </select>

              <div
                style={{
                  display: "flex",
                  gap: "10px",
                  justifyContent: "flex-end",
                }}
              >
                <button
                  type="button"
                  style={styles.btn}
                  onClick={() => setShowInvite(false)}
                >
                  Batal
                </button>
                <button type="submit" style={styles.btnPrimary}>
                  Buat User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}