-- ============================================================
-- BIthere Application Tables (Supabase PostgreSQL)
-- PRJ Section 5.2 - Auth & Metadata
-- Run this in Supabase SQL Editor.
-- ============================================================

create table if not exists profiles (
    id uuid primary key,
    email text,
    role text default 'analyst',
    created_at timestamptz default now()
);

create table if not exists dashboard_configs (
    id serial primary key,
    user_id uuid references profiles(id) on delete cascade,
    metabase_dashboard_id integer,
    config_json jsonb,
    embed_url text,
    created_at timestamptz default now()
);

create table if not exists query_history (
    id serial primary key,
    user_id uuid references profiles(id) on delete cascade,
    prompt text,
    generated_query text,
    status text,
    created_at timestamptz default now()
);

create table if not exists business_glossary (
    id serial primary key,
    term text not null,
    definition text,
    category text,
    created_at timestamptz default now()
);

create table if not exists ingestion_logs (
    id serial primary key,
    namespace text,
    record_count integer,
    status text,
    created_at timestamptz default now()
);

create index if not exists idx_dashboard_configs_user
    on dashboard_configs(user_id);

create index if not exists idx_query_history_user
    on query_history(user_id);

-- Seed admin profile (user sudah ada di Supabase Auth)
insert into profiles (id, email, role)
values (
    'fc01038e-c259-4854-9139-694d4d0a6eee',
    'adiikusuma1001@gmail.com',
    'admin'
)
on conflict (id) do update
    set email = excluded.email,
        role = excluded.role;