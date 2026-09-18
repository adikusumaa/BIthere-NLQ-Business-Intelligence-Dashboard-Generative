#!/usr/bin/env bash
set -euo pipefail

echo "[PROCESS] Creating BIthere v2 folder structure..."

# Backend
mkdir -p backend/app/workspace/secrets
mkdir -p backend/app/workspace/datasets
mkdir -p backend/app/workspace/schema_builder
mkdir -p backend/app/dashboard/prompts
mkdir -p backend/app/dashboard/tests

# Frontend
mkdir -p frontend/src/pages/wizard
mkdir -p frontend/src/pages/integrations
mkdir -p frontend/src/pages/datasets
mkdir -p frontend/src/pages/schema-builder
mkdir -p frontend/src/pages/knowledge-base
mkdir -p frontend/src/pages/workspace
mkdir -p frontend/src/components/dashboard-editor
mkdir -p frontend/src/store

# Scripts & migrations
mkdir -p scripts/migrations
mkdir -p uploads
mkdir -p duckdb
mkdir -p test

# Keep-empty markers
touch backend/app/workspace/__init__.py
touch backend/app/workspace/secrets/__init__.py
touch backend/app/workspace/datasets/__init__.py
touch backend/app/workspace/schema_builder/__init__.py
touch backend/app/dashboard/__init__.py
touch backend/app/dashboard/tests/__init__.py

echo "[SUCCESS] Folder structure created"