#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export PROVIDER="${PROVIDER:-glm-code}"
export BASE_URL="${BASE_URL:-https://open.bigmodel.cn/api/coding/paas/v4}"
export MODEL="${MODEL:-glm-5.1}"
export PORT="${PORT:-8082}"
export CRB_SERVICE_NAME="${CRB_SERVICE_NAME:-glm-public-coder}"

if [[ -n "${ZHIPU_API_KEY:-}" && -z "${API_KEY:-}" ]]; then
  export API_KEY="$ZHIPU_API_KEY"
fi

exec "$ROOT_DIR/scripts/start.sh"
