import { supabase } from "./supabase";

const API_BASE = import.meta.env.VITE_API_BASE_URL;

let activeWorkspaceId = null;

export function setActiveWorkspace(workspaceId) {
  activeWorkspaceId = workspaceId;
}

export function getActiveWorkspace() {
  return activeWorkspaceId;
}

async function getAuthToken() {
  const { data } = await supabase.auth.getSession();
  return data?.session?.access_token || null;
}

async function request(method, path, { body, workspaceId, raw } = {}) {
  const token = await getAuthToken();
  const headers = { Accept: "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;

  const wsId = workspaceId || activeWorkspaceId;
  if (wsId) headers["X-Workspace-ID"] = wsId;

  let payload;
  if (body instanceof FormData) {
    payload = body;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: payload,
  });

  if (raw) return response;

  if (response.status === 204) return null;

  const text = await response.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text };
    }
  }

  if (!response.ok) {
    const message = data?.detail || `HTTP ${response.status}`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return data;
}

export const api = {
  listWorkspaces: () => request("GET", "/api/workspaces"),
  createWorkspace: (payload) => request("POST", "/api/workspaces", { body: payload }),
  getWorkspace: (id) => request("GET", `/api/workspaces/${id}`),
  updateWorkspace: (id, payload) =>
    request("PATCH", `/api/workspaces/${id}`, { body: payload }),
  deleteWorkspace: (id) => request("DELETE", `/api/workspaces/${id}`),
  listMembers: (id) => request("GET", `/api/workspaces/${id}/members`),
  addMember: (id, payload) =>
    request("POST", `/api/workspaces/${id}/members`, { body: payload }),
  removeMember: (id, userId) =>
    request("DELETE", `/api/workspaces/${id}/members/${userId}`),

  createWorkspaceInvite: (wsId, email, role) =>
    request("POST", `/api/workspaces/${wsId}/invites`, {
      body: { email, role },
    }),
  listWorkspaceInvites: (wsId) =>
    request("GET", `/api/workspaces/${wsId}/invites`),
  revokeWorkspaceInvite: (wsId, inviteId) =>
    request("DELETE", `/api/workspaces/${wsId}/invites/${inviteId}`),

  listIntegrations: (wsId) => request("GET", `/api/integrations/${wsId}`),
  setIntegration: (wsId, service, value, metadata) =>
    request("POST", `/api/integrations/${wsId}/${service}`, {
      body: { value, metadata },
    }),
  testIntegration: (wsId, service, extra) =>
    request("POST", `/api/integrations/${wsId}/${service}/test`, {
      body: { extra },
    }),
  deleteIntegration: (wsId, service) =>
    request("DELETE", `/api/integrations/${wsId}/${service}`),
  testAllIntegrations: (wsId) =>
    request("POST", `/api/integrations/${wsId}/test-all`),

  listDataSources: (wsId) =>
    request("GET", `/api/workspaces/${wsId}/data-sources`),
  addDataSource: (wsId, payload) =>
    request("POST", `/api/workspaces/${wsId}/data-sources`, { body: payload }),
  testDataSource: (wsId, dsId) =>
    request("POST", `/api/workspaces/${wsId}/data-sources/${dsId}/test`),
  setDefaultDataSource: (wsId, dsId) =>
    request("POST", `/api/workspaces/${wsId}/data-sources/set-default`, {
      body: { ds_id: dsId },
    }),
  deleteDataSource: (wsId, dsId) =>
    request("DELETE", `/api/workspaces/${wsId}/data-sources/${dsId}`),

  listDatasets: (wsId) => request("GET", `/api/workspaces/${wsId}/datasets`),
  getDataset: (wsId, dsId) =>
    request("GET", `/api/workspaces/${wsId}/datasets/${dsId}`),
  previewDataset: (wsId, dsId, n = 100) =>
    request("GET", `/api/workspaces/${wsId}/datasets/${dsId}/preview?n=${n}`),
  deleteDataset: (wsId, dsId) =>
    request("DELETE", `/api/workspaces/${wsId}/datasets/${dsId}`),
  uploadDataset: (wsId, file, { name, target = "duckdb" } = {}) => {
    const form = new FormData();
    form.append("file", file);
    if (name) form.append("name", name);
    form.append("target", target);
    return request("POST", `/api/workspaces/${wsId}/datasets/upload`, {
      body: form,
    });
  },

  generateDDL: (wsId, payload) =>
    request("POST", `/api/workspaces/${wsId}/schema-builder/generate-ddl`, {
      body: payload,
    }),
  applySchema: (wsId, payload) =>
    request("POST", `/api/workspaces/${wsId}/schema-builder/apply`, {
      body: payload,
    }),
  rollbackSchema: (wsId, payload) =>
    request("POST", `/api/workspaces/${wsId}/schema-builder/rollback`, {
      body: payload,
    }),
  getSchemaForDataset: (wsId, datasetId) =>
    request("GET", `/api/workspaces/${wsId}/schema-builder/${datasetId}`),

  getWorkspaceSchema: (wsId) =>
    request("GET", `/api/workspaces/${wsId}/knowledge-base/schema`),
  listGlossary: (wsId) =>
    request("GET", `/api/workspaces/${wsId}/knowledge-base/glossary`),
  addGlossaryTerm: (wsId, payload) =>
    request("POST", `/api/workspaces/${wsId}/knowledge-base/glossary`, {
      body: payload,
    }),
  updateGlossaryTerm: (wsId, termId, payload) =>
    request("PATCH", `/api/workspaces/${wsId}/knowledge-base/glossary/${termId}`, {
      body: payload,
    }),
  deleteGlossaryTerm: (wsId, termId) =>
    request("DELETE", `/api/workspaces/${wsId}/knowledge-base/glossary/${termId}`),
  uploadGlossaryCsv: (wsId, file) => {
    const form = new FormData();
    form.append("file", file);
    return request("POST", `/api/workspaces/${wsId}/knowledge-base/glossary/upload-csv`, {
      body: form,
    });
  },
  reingest: (wsId) =>
    request("POST", `/api/workspaces/${wsId}/knowledge-base/reingest`),

  getWizardState: (wsId) =>
    request("GET", `/api/workspaces/${wsId}/wizard/state`),
  saveWizardStep: (wsId, step, data) =>
    request("POST", `/api/workspaces/${wsId}/wizard/step/${step}`, {
      body: { data },
    }),
  completeWizard: (wsId) =>
    request("POST", `/api/workspaces/${wsId}/wizard/complete`),
  resetWizard: (wsId) =>
    request("POST", `/api/workspaces/${wsId}/wizard/reset`),

  getDashboardState: (wsId, dashboardId) =>
    request("GET", `/api/workspaces/${wsId}/dashboards/${dashboardId}/state`),
  listDashboardVersions: (wsId, dashboardId) =>
    request("GET", `/api/workspaces/${wsId}/dashboards/${dashboardId}/versions`),
  getDashboardVersion: (wsId, dashboardId, version) =>
    request("GET", `/api/workspaces/${wsId}/dashboards/${dashboardId}/versions/${version}`),
  listDashboardPatches: (wsId, dashboardId, limit = 100) =>
    request("GET", `/api/workspaces/${wsId}/dashboards/${dashboardId}/patches?limit=${limit}`),
  parseDashboardPatch: (wsId, dashboardId, instruction) =>
    request("POST", `/api/workspaces/${wsId}/dashboards/${dashboardId}/patch/parse`, {
      body: { instruction },
    }),
  applyDashboardPatch: (wsId, dashboardId, { patch, instruction, base_version }) =>
    request("POST", `/api/workspaces/${wsId}/dashboards/${dashboardId}/patch/apply`, {
      body: { patch, instruction, base_version },
    }),
  manualEditDashboard: (wsId, dashboardId, { patch, base_version, session_id }) =>
    request("POST", `/api/workspaces/${wsId}/dashboards/${dashboardId}/manual-edit`, {
      body: { patch, base_version, session_id },
    }),
  rollbackDashboard: (wsId, dashboardId, { target_version, base_version }) =>
    request("POST", `/api/workspaces/${wsId}/dashboards/${dashboardId}/rollback`, {
      body: { target_version, base_version },
    }),
  diffDashboard: (wsId, dashboardId, v1, v2) =>
    request("GET", `/api/workspaces/${wsId}/dashboards/${dashboardId}/diff?v1=${v1}&v2=${v2}`),
  undoDashboard: (wsId, dashboardId, sessionId) =>
    request("POST", `/api/workspaces/${wsId}/dashboards/${dashboardId}/undo?session_id=${sessionId}`),
  redoDashboard: (wsId, dashboardId, sessionId) =>
    request("POST", `/api/workspaces/${wsId}/dashboards/${dashboardId}/redo?session_id=${sessionId}`),
  importDashboard: (wsId, metabase_dashboard_id) =>
    request("POST", `/api/workspaces/${wsId}/dashboards/import`, {
      body: { metabase_dashboard_id },
    }),
  getProgress: (key) => request("GET", `/api/progress/${key}`),
};