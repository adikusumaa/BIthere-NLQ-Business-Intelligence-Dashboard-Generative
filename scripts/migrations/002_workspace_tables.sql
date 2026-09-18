

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS workspaces (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    slug            TEXT UNIQUE NOT NULL,
    owner_id        UUID NOT NULL,
    plan            TEXT NOT NULL DEFAULT 'free',
    setup_progress  JSONB NOT NULL DEFAULT '{}'::jsonb,
    setup_completed BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_workspaces_owner ON workspaces(owner_id);

CREATE TABLE IF NOT EXISTS workspace_members (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id      UUID NOT NULL,
    role         TEXT NOT NULL CHECK (role IN ('owner','admin','analyst','viewer')),
    invited_by   UUID,
    joined_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_members_workspace ON workspace_members(workspace_id);
CREATE INDEX IF NOT EXISTS idx_members_user ON workspace_members(user_id);

CREATE TABLE IF NOT EXISTS workspace_secrets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    service         TEXT NOT NULL,
    encrypted_value TEXT NOT NULL,
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_used_at    TIMESTAMPTZ,
    rotated_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, service)
);
CREATE INDEX IF NOT EXISTS idx_secrets_workspace ON workspace_secrets(workspace_id);

CREATE TABLE IF NOT EXISTS workspace_data_sources (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id         UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name                 TEXT NOT NULL,
    type                 TEXT NOT NULL CHECK (type IN ('postgresql','mysql','mongodb','sqlite','duckdb')),
    encrypted_connection TEXT,
    config               JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_default           BOOLEAN NOT NULL DEFAULT false,
    last_tested_at       TIMESTAMPTZ,
    last_test_ok         BOOLEAN,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_datasources_workspace ON workspace_data_sources(workspace_id);

CREATE TABLE IF NOT EXISTS workspace_datasets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    source_type     TEXT NOT NULL CHECK (source_type IN ('csv','excel','parquet')),
    file_path       TEXT NOT NULL,
    file_size_bytes BIGINT,
    row_count       BIGINT,
    column_count    INTEGER,
    status          TEXT NOT NULL DEFAULT 'uploaded',
    target          TEXT NOT NULL DEFAULT 'duckdb' CHECK (target IN ('duckdb','supabase')),
    schema_applied  BOOLEAN NOT NULL DEFAULT false,
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by      UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_datasets_workspace ON workspace_datasets(workspace_id);

CREATE TABLE IF NOT EXISTS workspace_schemas (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    dataset_id      UUID REFERENCES workspace_datasets(id) ON DELETE CASCADE,
    table_name      TEXT NOT NULL,
    ddl             TEXT NOT NULL,
    columns_json    JSONB NOT NULL DEFAULT '[]'::jsonb,
    indexes_json    JSONB NOT NULL DEFAULT '[]'::jsonb,
    partitions_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    status          TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','applied','rolled_back')),
    applied_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_schemas_workspace ON workspace_schemas(workspace_id);

CREATE TABLE IF NOT EXISTS audit_logs (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id  UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id       UUID,
    action        TEXT NOT NULL,
    resource_type TEXT,
    resource_id   TEXT,
    detail        JSONB NOT NULL DEFAULT '{}'::jsonb,
    ip_address    TEXT,
    user_agent    TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_audit_workspace ON audit_logs(workspace_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS usage_events (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id   UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id        UUID,
    service        TEXT NOT NULL,
    event_type     TEXT NOT NULL,
    tokens_input   INTEGER DEFAULT 0,
    tokens_output  INTEGER DEFAULT 0,
    cost_estimate  NUMERIC(12,6) DEFAULT 0,
    request_id     TEXT,
    metadata       JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_usage_workspace ON usage_events(workspace_id, created_at DESC);


ALTER TABLE workspaces               ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspace_members        ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspace_secrets        ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspace_data_sources   ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspace_datasets       ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspace_schemas        ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs               ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_events             ENABLE ROW LEVEL SECURITY;

CREATE OR REPLACE FUNCTION is_workspace_member(ws_id UUID)
RETURNS BOOLEAN
LANGUAGE SQL SECURITY DEFINER AS $$
    SELECT EXISTS (
        SELECT 1 FROM workspace_members
        WHERE workspace_id = ws_id AND user_id = auth.uid()
    );
$$;

CREATE POLICY workspaces_select ON workspaces FOR SELECT
    USING (owner_id = auth.uid() OR is_workspace_member(id));
CREATE POLICY workspaces_insert ON workspaces FOR INSERT
    WITH CHECK (owner_id = auth.uid());
CREATE POLICY workspaces_update ON workspaces FOR UPDATE
    USING (owner_id = auth.uid());
CREATE POLICY workspaces_delete ON workspaces FOR DELETE
    USING (owner_id = auth.uid());

CREATE POLICY members_select ON workspace_members FOR SELECT
    USING (is_workspace_member(workspace_id));
CREATE POLICY members_write ON workspace_members FOR ALL
    USING (is_workspace_member(workspace_id))
    WITH CHECK (is_workspace_member(workspace_id));

CREATE POLICY secrets_all ON workspace_secrets FOR ALL
    USING (is_workspace_member(workspace_id))
    WITH CHECK (is_workspace_member(workspace_id));

CREATE POLICY datasources_all ON workspace_data_sources FOR ALL
    USING (is_workspace_member(workspace_id))
    WITH CHECK (is_workspace_member(workspace_id));

CREATE POLICY datasets_all ON workspace_datasets FOR ALL
    USING (is_workspace_member(workspace_id))
    WITH CHECK (is_workspace_member(workspace_id));

CREATE POLICY schemas_all ON workspace_schemas FOR ALL
    USING (is_workspace_member(workspace_id))
    WITH CHECK (is_workspace_member(workspace_id));

CREATE POLICY audit_select ON audit_logs FOR SELECT
    USING (is_workspace_member(workspace_id));
CREATE POLICY audit_insert ON audit_logs FOR INSERT
    WITH CHECK (is_workspace_member(workspace_id));

CREATE POLICY usage_select ON usage_events FOR SELECT
    USING (is_workspace_member(workspace_id));
CREATE POLICY usage_insert ON usage_events FOR INSERT
    WITH CHECK (is_workspace_member(workspace_id));
