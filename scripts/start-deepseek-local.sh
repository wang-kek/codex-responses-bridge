#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export PROVIDER="${PROVIDER:-deepseek}"
export BASE_URL="${BASE_URL:-http://127.0.0.1:8000/v1}"
export MODEL="${MODEL:-deepseek-v4-pro}"
export PORT="${PORT:-8096}"
export CRB_SERVICE_NAME="${CRB_SERVICE_NAME:-deepseek-local}"
export CRB_UPSTREAM_API_KEY_ENV="${CRB_UPSTREAM_API_KEY_ENV:-}"
export ALLOW_NO_API_KEY=1

exec "$ROOT_DIR/scripts/start.sh"
