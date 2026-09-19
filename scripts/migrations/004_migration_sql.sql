-- =====================================================
-- BIthere v2 - Migration 003: Dashboard Versions (F-13)
-- =====================================================

CREATE TABLE IF NOT EXISTS dashboard_versions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dashboard_id    UUID NOT NULL,
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    version         INTEGER NOT NULL,
    parent_version  INTEGER,
    state_json      JSONB NOT NULL,
    patch_applied   JSONB,
    created_by      UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (dashboard_id, version)
);

CREATE INDEX IF NOT EXISTS idx_versions_dashboard
    ON dashboard_versions(dashboard_id, version DESC);
CREATE INDEX IF NOT EXISTS idx_versions_workspace
    ON dashboard_versions(workspace_id, created_at DESC);

CREATE TABLE IF NOT EXISTS dashboard_patches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dashboard_id    UUID NOT NULL,
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    from_version    INTEGER NOT NULL,
    to_version      INTEGER NOT NULL,
    patch_json      JSONB NOT NULL,
    patch_hash      TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'applied'
                    CHECK (status IN ('applied','rejected','failed','rolled_back')),
    error_message   TEXT,
    created_by      UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_patches_dashboard
    ON dashboard_patches(dashboard_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_patches_workspace
    ON dashboard_patches(workspace_id, created_at DESC);

-- RLS
ALTER TABLE dashboard_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE dashboard_patches  ENABLE ROW LEVEL SECURITY;

CREATE POLICY versions_all ON dashboard_versions FOR ALL
    USING (is_workspace_member(workspace_id))
    WITH CHECK (is_workspace_member(workspace_id));

CREATE POLICY patches_all ON dashboard_patches FOR ALL
    USING (is_workspace_member(workspace_id))
    WITH CHECK (is_workspace_member(workspace_id));

-- =====================================================
-- END OF MIGRATION 003
-- =====================================================