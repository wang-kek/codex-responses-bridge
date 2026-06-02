#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv}"
APP_BIN="$VENV_DIR/bin/codex-responses-bridge"
CONFIG_FILE="${CONFIG_FILE:-$ROOT_DIR/configs/services.example.yaml}"
KEYS_FILE="${KEYS_FILE:-$ROOT_DIR/configs/model-keys.env}"
RUN_DIR="${RUN_DIR:-$ROOT_DIR/run}"
PID_FILE="${PID_FILE:-$RUN_DIR/codex-responses-bridge.pid}"
LOG_FILE="${LOG_FILE:-$RUN_DIR/codex-responses-bridge.log}"
DAEMON_MODE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --daemon|-d)
      DAEMON_MODE=1
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: ./scripts/start-all.sh [--daemon]" >&2
      exit 1
      ;;
  esac
done

choose_python_bin() {
  if [[ -n "${PYTHON_BIN:-}" ]]; then
    printf '%s\n' "$PYTHON_BIN"
    return 0
  fi

  local candidate
  for candidate in python python3 python3.12 python3.11 python3.10 python3.9 python3.8; do
    if ! command -v "$candidate" >/dev/null 2>&1; then
      continue
    fi
    if "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)' >/dev/null 2>&1; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  echo "No compatible Python 3.8+ interpreter found. Set PYTHON_BIN explicitly, for example: PYTHON_BIN=python ./scripts/start-all.sh" >&2
  return 1
}

PYTHON_BIN="$(choose_python_bin)"

if [[ "${CONFIG_FILE:-}" == "$ROOT_DIR/configs/services.example.yaml" && -f "$ROOT_DIR/configs/services.yaml" ]]; then
  CONFIG_FILE="$ROOT_DIR/configs/services.yaml"
fi
if [[ "${KEYS_FILE:-}" == "$ROOT_DIR/configs/model-keys.env" && ! -f "$KEYS_FILE" && -f "$ROOT_DIR/configs/model-keys.env.example" ]]; then
  KEYS_FILE="$ROOT_DIR/configs/model-keys.env.example"
fi

if [[ ! -x "$APP_BIN" ]]; then
  if [[ ! -d "$VENV_DIR" ]]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  fi
  "$VENV_DIR/bin/python" -m pip install --upgrade pip
  "$VENV_DIR/bin/pip" install -e "$ROOT_DIR"
fi

if [[ -f "$KEYS_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$KEYS_FILE"
  set +a
fi

export CRB_USE_CONFIG_FILE=1
export CRB_CONFIG_FILE="$CONFIG_FILE"

if [[ "$DAEMON_MODE" == "1" ]]; then
  mkdir -p "$RUN_DIR"

  if [[ -f "$PID_FILE" ]]; then
    OLD_PID="$(cat "$PID_FILE" 2>/dev/null || true)"
    if [[ -n "$OLD_PID" ]] && kill -0 "$OLD_PID" >/dev/null 2>&1; then
      echo "codex-responses-bridge is already running, pid=$OLD_PID" >&2
      exit 1
    fi
    rm -f "$PID_FILE"
  fi

  nohup "$APP_BIN" >>"$LOG_FILE" 2>&1 &
  NEW_PID=$!
  echo "$NEW_PID" > "$PID_FILE"
  echo "codex-responses-bridge started in background, pid=$NEW_PID"
  echo "log file: $LOG_FILE"
  exit 0
fi

exec "$APP_BIN"
