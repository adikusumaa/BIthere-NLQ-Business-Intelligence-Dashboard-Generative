CREATE TABLE IF NOT EXISTS workspace_glossary (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    term            TEXT NOT NULL,
    definition      TEXT NOT NULL,
    category        TEXT,
    synonyms        TEXT[] DEFAULT '{}',
    source          TEXT NOT NULL DEFAULT 'manual',
    created_by      UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, term)
);
CREATE INDEX IF NOT EXISTS idx_glossary_workspace ON workspace_glossary(workspace_id);

ALTER TABLE workspace_glossary ENABLE ROW LEVEL SECURITY;
CREATE POLICY glossary_all ON workspace_glossary FOR ALL
    USING (is_workspace_member(workspace_id))
    WITH CHECK (is_workspace_member(workspace_id));