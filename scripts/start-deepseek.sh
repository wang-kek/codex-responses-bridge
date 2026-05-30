#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export PROVIDER="${PROVIDER:-deepseek}"
export BASE_URL="${BASE_URL:-https://api.deepseek.com/v1}"
export MODEL="${MODEL:-deepseek-v4-pro}"
export PORT="${PORT:-8093}"
export CRB_SERVICE_NAME="${CRB_SERVICE_NAME:-deepseek-public}"

if [[ -n "${DEEPSEEK_API_KEY:-}" && -z "${API_KEY:-}" ]]; then
  export API_KEY="$DEEPSEEK_API_KEY"
fi

exec "$ROOT_DIR/scripts/start.sh"
