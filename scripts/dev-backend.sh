#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../services/api"
uv run uvicorn app.main:app --reload
