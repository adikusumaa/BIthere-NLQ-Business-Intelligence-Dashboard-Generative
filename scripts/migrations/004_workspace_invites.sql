CREATE TABLE IF NOT EXISTS workspace_invites (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    email           TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('admin','analyst','viewer')),
    invited_by      UUID,
    status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','accepted','revoked')),
    accepted_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (workspace_id, email)
);

CREATE INDEX IF NOT EXISTS idx_invites_workspace ON workspace_invites(workspace_id);
CREATE INDEX IF NOT EXISTS idx_invites_email_status ON workspace_invites(email, status);

ALTER TABLE workspace_invites ENABLE ROW LEVEL SECURITY;

CREATE POLICY invites_all ON workspace_invites FOR ALL
    USING (is_workspace_member(workspace_id))
    WITH CHECK (is_workspace_member(workspace_id));