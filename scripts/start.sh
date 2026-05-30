#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv}"
APP_BIN="$VENV_DIR/bin/codex-responses-bridge"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if [[ ! -x "$APP_BIN" ]]; then
  if [[ ! -d "$VENV_DIR" ]]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  fi
  "$VENV_DIR/bin/python" -m pip install --upgrade pip
  "$VENV_DIR/bin/pip" install -e "$ROOT_DIR"
fi

if [[ -n "${PORT:-}" ]]; then export CRB_PORT="$PORT"; fi
if [[ -n "${HOST:-}" ]]; then export CRB_HOST="$HOST"; fi
if [[ -n "${LANGUAGE:-}" ]]; then export CRB_LANGUAGE="$LANGUAGE"; fi
if [[ -n "${PROVIDER:-}" ]]; then export CRB_UPSTREAM_PROVIDER="$PROVIDER"; fi
if [[ -n "${BASE_URL:-}" ]]; then export CRB_UPSTREAM_BASE_URL="$BASE_URL"; fi
if [[ -n "${MODEL:-}" ]]; then export CRB_UPSTREAM_MODEL="$MODEL"; fi
if [[ -n "${API_KEY:-}" ]]; then export CRB_UPSTREAM_API_KEY="$API_KEY"; fi
if [[ -n "${MM_PROVIDER:-}" ]]; then export CRB_MM_UPSTREAM_PROVIDER="$MM_PROVIDER"; fi
if [[ -n "${MM_BASE_URL:-}" ]]; then export CRB_MM_UPSTREAM_BASE_URL="$MM_BASE_URL"; fi
if [[ -n "${MM_MODEL:-}" ]]; then export CRB_MM_UPSTREAM_MODEL="$MM_MODEL"; fi
if [[ -n "${MM_API_KEY:-}" ]]; then export CRB_MM_UPSTREAM_API_KEY="$MM_API_KEY"; fi
if [[ -n "${MODEL_ALIASES_JSON:-}" ]]; then export CRB_MODEL_ALIASES_JSON="$MODEL_ALIASES_JSON"; fi
if [[ -n "${CAPTURE_ENABLED:-}" ]]; then export CRB_CAPTURE_ENABLED="$CAPTURE_ENABLED"; fi
if [[ -n "${CAPTURE_DIR:-}" ]]; then export CRB_CAPTURE_DIR="$CAPTURE_DIR"; fi

if [[ -z "${CRB_UPSTREAM_API_KEY:-}" && -z "${API_KEY:-}" ]]; then
  echo "Missing API key. Start with API_KEY=xxx, for example:" >&2
  echo "  API_KEY=your-key PROVIDER=glm-code MODEL=glm-5.1 ./scripts/start.sh" >&2
  exit 1
fi

exec "$APP_BIN"
