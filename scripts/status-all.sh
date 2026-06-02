#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="${RUN_DIR:-$ROOT_DIR/run}"
PID_FILE="${PID_FILE:-$RUN_DIR/codex-responses-bridge.pid}"
LOG_FILE="${LOG_FILE:-$RUN_DIR/codex-responses-bridge.log}"

if [[ ! -f "$PID_FILE" ]]; then
  echo "codex-responses-bridge: stopped"
  echo "pid file: $PID_FILE"
  echo "log file: $LOG_FILE"
  exit 0
fi

PID="$(cat "$PID_FILE" 2>/dev/null || true)"
if [[ -z "$PID" ]]; then
  echo "codex-responses-bridge: unknown"
  echo "pid file is empty: $PID_FILE"
  echo "log file: $LOG_FILE"
  exit 1
fi

if kill -0 "$PID" >/dev/null 2>&1; then
  echo "codex-responses-bridge: running"
  echo "pid: $PID"
  echo "log file: $LOG_FILE"
  exit 0
fi

echo "codex-responses-bridge: stale pid file"
echo "pid: $PID"
echo "log file: $LOG_FILE"
exit 1
