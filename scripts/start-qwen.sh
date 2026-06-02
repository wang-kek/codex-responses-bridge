#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export PROVIDER="${PROVIDER:-qwen37-token}"
export BASE_URL="${BASE_URL:-https://dashscope.aliyuncs.com/compatible-mode/v1}"
export MODEL="${MODEL:-qwen3.7-max}"
export PORT="${PORT:-8084}"
export CRB_SERVICE_NAME="${CRB_SERVICE_NAME:-qwen-public}"

if [[ -n "${DASHSCOPE_API_KEY:-}" && -z "${API_KEY:-}" ]]; then
  export API_KEY="$DASHSCOPE_API_KEY"
fi

exec "$ROOT_DIR/scripts/start.sh"
