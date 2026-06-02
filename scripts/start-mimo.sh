#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export PROVIDER="${PROVIDER:-mimo}"
export BASE_URL="${BASE_URL:-https://api.xiaomimimo.com/v1}"
export MODEL="${MODEL:-mimo-v2.5-pro}"
export PORT="${PORT:-8085}"
export CRB_SERVICE_NAME="${CRB_SERVICE_NAME:-mimo-public}"

if [[ -n "${MIMO_API_KEY:-}" && -z "${API_KEY:-}" ]]; then
  export API_KEY="$MIMO_API_KEY"
fi

exec "$ROOT_DIR/scripts/start.sh"
