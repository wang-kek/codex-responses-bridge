#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="${RUN_DIR:-$ROOT_DIR/run}"
PID_FILE="${PID_FILE:-$RUN_DIR/codex-responses-bridge.pid}"
WAIT_SECONDS="${WAIT_SECONDS:-10}"

if [[ ! -f "$PID_FILE" ]]; then
  echo "No pid file found: $PID_FILE"
  exit 0
fi

PID="$(cat "$PID_FILE" 2>/dev/null || true)"
if [[ -z "$PID" ]]; then
  echo "Pid file is empty: $PID_FILE" >&2
  rm -f "$PID_FILE"
  exit 1
fi

if ! kill -0 "$PID" >/dev/null 2>&1; then
  echo "Process not running, removing stale pid file: $PID"
  rm -f "$PID_FILE"
  exit 0
fi

kill "$PID"

for _ in $(seq 1 "$WAIT_SECONDS"); do
  if ! kill -0 "$PID" >/dev/null 2>&1; then
    rm -f "$PID_FILE"
    echo "codex-responses-bridge stopped, pid=$PID"
    exit 0
  fi
  sleep 1
done

echo "Process did not stop within ${WAIT_SECONDS}s, sending SIGKILL: pid=$PID" >&2
kill -9 "$PID" >/dev/null 2>&1 || true
rm -f "$PID_FILE"
echo "codex-responses-bridge killed, pid=$PID"
