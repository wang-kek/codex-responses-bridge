#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export PROVIDER="${PROVIDER:-deepseek}"
export BASE_URL="${BASE_URL:-http://127.0.0.1:8000/v1}"
export MODEL="${MODEL:-deepseek-v4-flash}"
export PORT="${PORT:-8081}"
export CRB_SERVICE_NAME="${CRB_SERVICE_NAME:-deepseek-local}"
export MM_PROVIDER="${MM_PROVIDER:-local-vlm}"
export MM_BASE_URL="${MM_BASE_URL:-http://192.168.1.251:33338/v1}"
export MM_MODEL="${MM_MODEL:-Qwen/Qwen3-VL-8B-Instruct}"
export MM_API_KEY_ENV="${MM_API_KEY_ENV:-LOCAL_VLM_API_KEY}"
# 本地服务通常不需要 key；如果需要，可用 DEEPSEEK_LOCAL_API_KEY=xxx 传入。
export CRB_UPSTREAM_API_KEY_ENV="${CRB_UPSTREAM_API_KEY_ENV:-DEEPSEEK_LOCAL_API_KEY}"
export ALLOW_NO_API_KEY=1

if [[ -n "${LOCAL_VLM_API_KEY:-}" && -z "${MM_API_KEY:-}" ]]; then
  export MM_API_KEY="$LOCAL_VLM_API_KEY"
fi

exec "$ROOT_DIR/scripts/start.sh"
