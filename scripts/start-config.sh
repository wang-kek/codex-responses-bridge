#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv}"
APP_BIN="$VENV_DIR/bin/codex-responses-bridge"
CONFIG_FILE="${CONFIG_FILE:-$ROOT_DIR/configs/services.example.yaml}"

if [[ ! -x "$APP_BIN" ]]; then
  echo "Missing executable: $APP_BIN" >&2
  echo "Run scripts/bootstrap.sh first." >&2
  exit 1
fi

export CRB_USE_CONFIG_FILE=1
export CRB_CONFIG_FILE="$CONFIG_FILE"

exec "$APP_BIN"
