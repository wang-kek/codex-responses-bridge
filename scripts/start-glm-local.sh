#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export PROVIDER="${PROVIDER:-glm-code}"
export BASE_URL="${BASE_URL:-http://192.168.1.232:8000/v1}"
export MODEL="${MODEL:-glm-5.1-fp8}"
export PORT="${PORT:-8080}"
export CRB_SERVICE_NAME="${CRB_SERVICE_NAME:-glm-local-main}"
export MM_PROVIDER="${MM_PROVIDER:-local-vlm}"
export MM_BASE_URL="${MM_BASE_URL:-http://192.168.1.251:33338/v1}"
export MM_MODEL="${MM_MODEL:-Qwen/Qwen3-VL-8B-Instruct}"
export MM_API_KEY_ENV="${MM_API_KEY_ENV:-LOCAL_VLM_API_KEY}"

if [[ -n "${LOCAL_GLM_API_KEY:-}" && -z "${API_KEY:-}" ]]; then
  export API_KEY="$LOCAL_GLM_API_KEY"
fi

if [[ -n "${LOCAL_VLM_API_KEY:-}" && -z "${MM_API_KEY:-}" ]]; then
  export MM_API_KEY="$LOCAL_VLM_API_KEY"
fi

exec "$ROOT_DIR/scripts/start.sh"
