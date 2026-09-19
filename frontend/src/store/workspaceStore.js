/**
 * Workspace store: active workspace + list + switching.
 * Auto-creates a default workspace on first login.
 * Tracks `initialized` to prevent race-condition redirects.
 */

import { create } from "zustand";
import { api, setActiveWorkspace } from "../services/api";

const STORAGE_KEY = "bithere-active-workspace";

export const useWorkspaceStore = create((set, get) => ({
  workspaces: [],
  activeWorkspace: null,
  loading: false,
  initialized: false,
  error: null,

  setActive: (workspace) => {
    if (workspace) {
      localStorage.setItem(STORAGE_KEY, workspace.id);
      setActiveWorkspace(workspace.id);
    } else {
      localStorage.removeItem(STORAGE_KEY);
      setActiveWorkspace(null);
    }
    set({ activeWorkspace: workspace });
  },

  loadWorkspaces: async () => {
    set({ loading: true, error: null });
    try {
      let workspaces = await api.listWorkspaces();

      // Auto-create default workspace on first login
      if (workspaces.length === 0) {
        const created = await api.createWorkspace({
          name: "My Workspace",
          plan: "free",
        });
        workspaces = [created];
      }

      const storedId = localStorage.getItem(STORAGE_KEY);
      let active =
        workspaces.find((w) => w.id === storedId) || workspaces[0] || null;

      if (active) {
        setActiveWorkspace(active.id);
        localStorage.setItem(STORAGE_KEY, active.id);
      }

      set({
        workspaces,
        activeWorkspace: active,
        loading: false,
        initialized: true,
      });
      return workspaces;
    } catch (err) {
      set({ error: err.message, loading: false, initialized: true });
      return [];
    }
  },

  createWorkspace: async (name) => {
    const ws = await api.createWorkspace({ name, plan: "free" });
    set((s) => ({
      workspaces: [...s.workspaces, ws],
    }));
    get().setActive(ws);
    return ws;
  },

  refreshWorkspace: async (id) => {
    const ws = await api.getWorkspace(id);
    set((s) => ({
      workspaces: s.workspaces.map((w) => (w.id === id ? { ...w, ...ws } : w)),
      activeWorkspace:
        s.activeWorkspace?.id === id
          ? { ...s.activeWorkspace, ...ws }
          : s.activeWorkspace,
    }));
    return ws;
  },

  clear: () => {
    localStorage.removeItem(STORAGE_KEY);
    setActiveWorkspace(null);
    set({ workspaces: [], activeWorkspace: null, initialized: false });
  },
}));