import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { ChevronRightIcon, PlusIcon, TrashIcon } from "../components/Icons";
import { api } from "../services/api";
import { useAuthStore } from "../store/authStore";
import { useWorkspaceStore } from "../store/workspaceStore";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const styles = {
  page: { minHeight: "100vh", background: "var(--ios-bg)" },
  header: {
    background: "var(--ios-surface)",
    borderBottom: "1px solid var(--ios-separator)",
    padding: "12px 20px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "16px",
  },
  brand: { display: "flex", alignItems: "center", gap: "12px" },
  avatar: {
    width: "36px", height: "36px", borderRadius: "50%",
    background: "linear-gradient(135deg, #5856D6 0%, #AF52DE 100%)",
    display: "flex", alignItems: "center", justifyContent: "center",
    color: "#FFFFFF", fontSize: "15px", fontWeight: "700",
    boxShadow: "0 2px 8px rgba(88, 86, 214, 0.24)",
  },
  brandText: { display: "flex", flexDirection: "column", lineHeight: 1.2 },
  brandName: { fontSize: "17px", fontWeight: "600", color: "var(--ios-text)", letterSpacing: "-0.02em" },
  brandTag: { fontSize: "12px", color: "var(--ios-text-secondary)" },
  actions: { display: "flex", alignItems: "center", gap: "8px" },
  container: { maxWidth: "760px", margin: "0 auto", padding: "24px 20px 60px" },
  largeTitle: { fontSize: "34px", fontWeight: "700", letterSpacing: "-0.03em", color: "var(--ios-text)", marginBottom: "4px" },
  subtitle: { fontSize: "15px", color: "var(--ios-text-secondary)", marginBottom: "28px" },
  tabs: { display: "flex", gap: 8, marginBottom: 20 },
  tab: (active) => ({
    padding: "8px 16px", borderRadius: 8, fontSize: 14, cursor: "pointer",
    border: "1px solid", borderColor: active ? "#3b82f6" : "var(--ios-separator)",
    background: active ? "#3b82f6" : "transparent",
    color: active ? "white" : "inherit",
  }),
  toolbar: { display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "20px" },
  countLabel: { fontSize: "15px", color: "var(--ios-text-secondary)" },
  groupWrap: { marginBottom: "28px" },
  groupLabel: {
    fontSize: "13px", fontWeight: "400", color: "var(--ios-text-secondary)",
    textTransform: "uppercase", letterSpacing: "0.06em",
    padding: "0 20px 8px 20px",
  },
  group: {
    background: "var(--ios-surface)", borderRadius: "var(--radius-md)",
    overflow: "hidden", boxShadow: "var(--shadow-xs)",
    border: "1px solid var(--ios-separator)",
  },
  userRow: {
    display: "flex", alignItems: "center", gap: "14px",
    padding: "14px 16px", borderBottom: "1px solid var(--ios-separator)",
  },
  userRowLast: { borderBottom: "none" },
  userAvatar: (role) => ({
    width: "40px", height: "40px", borderRadius: "50%",
    display: "flex", alignItems: "center", justifyContent: "center",
    color: "#FFFFFF", fontSize: "16px", fontWeight: "600",
    background: role === "admin"
      ? "linear-gradient(135deg, #007AFF 0%, #5856D6 100%)"
      : "linear-gradient(135deg, #8E8E93 0%, #C7C7CC 100%)",
    flexShrink: 0,
  }),
  userInfo: { flex: 1, minWidth: 0 },
  userEmail: {
    fontSize: "16px", fontWeight: "500", color: "var(--ios-text)",
    overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
  },
  userMeta: {
    fontSize: "13px", color: "var(--ios-text-secondary)",
    marginTop: "2px", display: "flex", alignItems: "center", gap: "8px",
  },
  roleBadge: (role) => ({
    display: "inline-block", padding: "2px 8px", borderRadius: "6px",
    fontSize: "11px", fontWeight: "600", letterSpacing: "0.02em",
    background: role === "admin" ? "rgba(0, 122, 255, 0.12)" : "rgba(142, 142, 147, 0.14)",
    color: role === "admin" ? "var(--ios-blue)" : "var(--ios-text-secondary)",
    textTransform: "uppercase",
  }),
  actionRow: { display: "flex", alignItems: "center", gap: "6px" },
  iconBtn: (variant) => ({
    width: "34px", height: "34px", borderRadius: "50%",
    display: "flex", alignItems: "center", justifyContent: "center",
    background: "var(--ios-surface-2)",
    color: variant === "danger" ? "var(--ios-red)" : "var(--ios-text-secondary)",
    transition: "background 0.15s ease",
  }),
  status: (ok) => ({
    padding: "12px 16px", borderRadius: "var(--radius-md)", fontSize: "14px",
    marginBottom: "20px",
    background: ok ? "rgba(52, 199, 89, 0.10)" : "rgba(255, 59, 48, 0.10)",
    color: ok ? "var(--ios-green)" : "var(--ios-red)",
    border: `1px solid ${ok ? "rgba(52, 199, 89, 0.24)" : "rgba(255, 59, 48, 0.24)"}`,
  }),
  modal: {
    position: "fixed", inset: 0, background: "rgba(0, 0, 0, 0.4)",
    backdropFilter: "blur(6px)", display: "flex",
    alignItems: "flex-end", justifyContent: "center",
    zIndex: 1000, padding: "20px",
  },
  sheet: {
    width: "100%", maxWidth: "440px", background: "var(--ios-surface)",
    borderRadius: "var(--radius-xl)", padding: "28px 24px 24px",
    boxShadow: "var(--shadow-lg)",
  },
  sheetTitle: { fontSize: "20px", fontWeight: "700", textAlign: "center", letterSpacing: "-0.02em", marginBottom: "4px" },
  sheetSubtitle: { fontSize: "13px", color: "var(--ios-text-secondary)", textAlign: "center", marginBottom: "24px" },
  label: {
    display: "block", fontSize: "12px", fontWeight: "600",
    color: "var(--ios-text-secondary)", marginBottom: "8px",
    letterSpacing: "0.04em", textTransform: "uppercase",
  },
  select: {
    width: "100%", padding: "14px 16px", fontSize: "16px",
    background: "var(--ios-surface-2)",
    border: "1px solid var(--ios-separator)",
    borderRadius: "var(--radius-md)", color: "var(--ios-text)",
    marginBottom: "16px", appearance: "none",
  },
  sheetActions: { display: "flex", gap: "10px", marginTop: "12px" },
};

export default function Admin() {
  const navigate = useNavigate();
  const role = useAuthStore((s) => s.role);
  const user = useAuthStore((s) => s.user);
  const getToken = useAuthStore((s) => s.getToken);
  const logout = useAuthStore((s) => s.logout);

  const activeWorkspace = useWorkspaceStore((s) => s.activeWorkspace);
  const workspaces = useWorkspaceStore((s) => s.workspaces);

  const [tab, setTab] = useState("users");

  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [showInvite, setShowInvite] = useState(false);
  const [inviteForm, setInviteForm] = useState({ email: "", role: "analyst", password: "" });

  const [invites, setInvites] = useState([]);
  const [inviteWsId, setInviteWsId] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("analyst");
  const [inviteLoading, setInviteLoading] = useState(false);

  useEffect(() => {
    if (role && role !== "admin") navigate("/chat");
  }, [role, navigate]);

  useEffect(() => {
    if (activeWorkspace?.id && !inviteWsId) setInviteWsId(activeWorkspace.id);
  }, [activeWorkspace, inviteWsId]);

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

  const loadInvites = async (wsId) => {
    if (!wsId) return;
    try {
      const list = await api.listWorkspaceInvites(wsId);
      setInvites(list || []);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => { loadUsers(); }, []);
  useEffect(() => { if (inviteWsId) loadInvites(inviteWsId); }, [inviteWsId]);

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
      if (!response.ok) throw new Error(data.detail || `HTTP ${response.status}`);
      setSuccess(`User ${data.email} created successfully.`);
      setShowInvite(false);
      setInviteForm({ email: "", role: "analyst", password: "" });
      loadUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleWorkspaceInvite = async (event) => {
    event.preventDefault();
    if (!inviteWsId || !inviteEmail) return;
    setError(null);
    setSuccess(null);
    setInviteLoading(true);
    try {
      await api.createWorkspaceInvite(inviteWsId, inviteEmail, inviteRole);
      setSuccess(`Invite sent to ${inviteEmail}`);
      setInviteEmail("");
      loadInvites(inviteWsId);
    } catch (err) {
      setError(err.message);
    } finally {
      setInviteLoading(false);
    }
  };

  const handleRevokeInvite = async (inviteId) => {
    try {
      await api.revokeWorkspaceInvite(inviteWsId, inviteId);
      loadInvites(inviteWsId);
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
      setSuccess(`Role updated to ${newRole}.`);
      loadUsers();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (userId, email) => {
    if (!window.confirm(`Delete user ${email}?`)) return;
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
      setSuccess(`User ${email} deleted.`);
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
          <div style={styles.avatar}>
            {user?.email ? user.email[0].toUpperCase() : "A"}
          </div>
          <div style={styles.brandText}>
            <div style={styles.brandName}>Admin Panel</div>
            <div style={styles.brandTag}>{user?.email || "Administrator"}</div>
          </div>
        </div>
        <div style={styles.actions}>
          <Link
            to="/chat"
            className="ios-btn-ghost"
            style={{ padding: "6px 12px", fontSize: "14px", borderRadius: "var(--radius-pill)" }}
          >
            Back to Chat
          </Link>
          <button
            className="ios-btn-ghost"
            onClick={handleLogout}
            style={{ padding: "6px 12px", fontSize: "14px", borderRadius: "var(--radius-pill)" }}
          >
            Logout
          </button>
        </div>
      </header>

      <div style={styles.container}>
        <h1 style={styles.largeTitle}>Administration</h1>
        <div style={styles.subtitle}>Manage users, workspaces, and invitations.</div>

        <div style={styles.tabs}>
          <button style={styles.tab(tab === "users")} onClick={() => setTab("users")}>Users</button>
          <button style={styles.tab(tab === "invites")} onClick={() => setTab("invites")}>Workspace Invites</button>
        </div>

        {error && <div style={styles.status(false)}>{error}</div>}
        {success && <div style={styles.status(true)}>{success}</div>}

        {tab === "users" && (
          <>
            <div style={styles.toolbar}>
              <span style={styles.countLabel}>
                {loading ? "Loading..." : `${users.length} user${users.length === 1 ? "" : "s"}`}
              </span>
              <button
                className="ios-btn ios-btn-pill"
                onClick={() => setShowInvite(true)}
                style={{ padding: "8px 16px", fontSize: "14px" }}
              >
                <PlusIcon size={16} color="#FFFFFF" />
                Create User
              </button>
            </div>

            <div style={styles.groupWrap}>
              <div style={styles.groupLabel}>All Users</div>
              <div style={styles.group}>
                {users.map((u, idx) => (
                  <div
                    key={u.id}
                    style={{
                      ...styles.userRow,
                      ...(idx === users.length - 1 ? styles.userRowLast : {}),
                    }}
                  >
                    <div style={styles.userAvatar(u.role)}>
                      {u.email ? u.email[0].toUpperCase() : "U"}
                    </div>
                    <div style={styles.userInfo}>
                      <div style={styles.userEmail}>{u.email}</div>
                      <div style={styles.userMeta}>
                        <span style={styles.roleBadge(u.role)}>{u.role}</span>
                      </div>
                    </div>
                    <div style={styles.actionRow}>
                      <button
                        className="ios-btn-ghost"
                        onClick={() =>
                          handleRoleChange(u.id, u.role === "admin" ? "analyst" : "admin")
                        }
                        disabled={u.id === user?.id}
                        style={{ padding: "6px 10px", fontSize: "13px", borderRadius: "8px" }}
                      >
                        {u.role === "admin" ? "Demote" : "Promote"}
                      </button>
                      <button
                        style={styles.iconBtn("danger")}
                        onClick={() => handleDelete(u.id, u.email)}
                        disabled={u.id === user?.id}
                      >
                        <TrashIcon size={14} color="var(--ios-red)" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {tab === "invites" && (
          <>
            <div style={styles.groupWrap}>
              <div style={styles.groupLabel}>Select Workspace</div>
              <select
                style={styles.select}
                value={inviteWsId}
                onChange={(e) => setInviteWsId(e.target.value)}
              >
                <option value="">-- choose workspace --</option>
                {workspaces.map((w) => (
                  <option key={w.id} value={w.id}>{w.name}</option>
                ))}
              </select>
            </div>

            {inviteWsId && (
              <>
                <div style={styles.groupWrap}>
                  <div style={styles.groupLabel}>Send Invite</div>
                  <form onSubmit={handleWorkspaceInvite} style={{ display: "flex", gap: 8, marginBottom: 20 }}>
                    <input
                      className="ios-input"
                      type="email"
                      placeholder="user@example.com"
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      required
                      style={{ flex: 1 }}
                    />
                    <select
                      style={{ ...styles.select, width: 140, marginBottom: 0 }}
                      value={inviteRole}
                      onChange={(e) => setInviteRole(e.target.value)}
                    >
                      <option value="analyst">Analyst</option>
                      <option value="viewer">Viewer</option>
                    </select>
                    <button
                      type="submit"
                      className="ios-btn"
                      disabled={inviteLoading}
                      style={{ padding: "12px 20px" }}
                    >
                      {inviteLoading ? "..." : "Invite"}
                    </button>
                  </form>
                </div>

                <div style={styles.groupWrap}>
                  <div style={styles.groupLabel}>Pending Invites</div>
                  <div style={styles.group}>
                    {invites.length === 0 ? (
                      <div style={{ padding: 16, fontSize: 14, color: "var(--ios-text-secondary)" }}>
                        No pending invites.
                      </div>
                    ) : (
                      invites.map((inv, idx) => (
                        <div
                          key={inv.id}
                          style={{
                            ...styles.userRow,
                            ...(idx === invites.length - 1 ? styles.userRowLast : {}),
                          }}
                        >
                          <div style={styles.userInfo}>
                            <div style={styles.userEmail}>{inv.email}</div>
                            <div style={styles.userMeta}>
                              <span style={styles.roleBadge(inv.role)}>{inv.role}</span>
                              <span>{inv.status}</span>
                            </div>
                          </div>
                          <button
                            style={styles.iconBtn("danger")}
                            onClick={() => handleRevokeInvite(inv.id)}
                          >
                            <TrashIcon size={14} color="var(--ios-red)" />
                          </button>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </>
            )}
          </>
        )}
      </div>

      {showInvite && (
        <div style={styles.modal} onClick={() => setShowInvite(false)}>
          <div style={styles.sheet} onClick={(e) => e.stopPropagation()}>
            <div style={styles.sheetTitle}>Create User</div>
            <div style={styles.sheetSubtitle}>
              Create a new account with a temporary password.
            </div>
            <form onSubmit={handleInvite}>
              <label style={styles.label}>Email</label>
              <input
                className="ios-input"
                type="email"
                value={inviteForm.email}
                onChange={(e) => setInviteForm((s) => ({ ...s, email: e.target.value }))}
                placeholder="user@example.com"
                required
                autoFocus
                style={{ marginBottom: "16px" }}
              />

              <label style={styles.label}>Temporary Password</label>
              <input
                className="ios-input"
                type="text"
                value={inviteForm.password}
                onChange={(e) => setInviteForm((s) => ({ ...s, password: e.target.value }))}
                placeholder="Minimum 6 characters"
                minLength={6}
                required
                style={{ marginBottom: "16px" }}
              />

              <label style={styles.label}>Role</label>
              <select
                style={styles.select}
                value={inviteForm.role}
                onChange={(e) => setInviteForm((s) => ({ ...s, role: e.target.value }))}
              >
                <option value="analyst">Analyst</option>
                <option value="admin">Admin</option>
              </select>

              <div style={styles.sheetActions}>
                <button
                  type="button"
                  className="ios-btn ios-btn-secondary"
                  onClick={() => setShowInvite(false)}
                  style={{ flex: 1 }}
                >
                  Cancel
                </button>
                <button type="submit" className="ios-btn" style={{ flex: 1 }}>
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}