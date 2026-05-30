# codex-responses-bridge

A lightweight multi-upstream bridge for Codex `Responses API`.

## Purpose

This project is focused on one job:

- accept Codex `/v1/responses`
- translate them into upstream model protocols
- support OpenAI-style `/v1/chat/completions` first
- keep a clean extension point for future Anthropic support

## Current capabilities

- target runtime: `Python 3.8+`
- lightweight `FastAPI + Uvicorn` service bootstrap
- single-service startup from environment variables
- multi-port startup from a YAML config file
- YAML supports `defaults` and reusable `upstreams` to reduce duplication
- separate text and multimodal upstreams under the same local port
- client model alias mapping such as `GPT-5.4` / `GPT-5.5` to internal upstream model names
- provider-specific GPT-name presets instead of one shared default mapping for all vendors
- unknown client model names fall back to the service default upstream model by default
- `Responses -> OpenAI Chat Completions` request translation
- non-stream `OpenAI Chat -> Responses` translation
- streaming `OpenAI Chat SSE -> Responses SSE` translation
- provider-profile-based field sanitization for upstream compatibility
- a separate provider-adapter layer for vendor-specific request rewrite rules
- `/v1/models` exposure for both client aliases and canonical upstream models
- built-in logging and protocol capture
- Chinese-first docs with English support

## License

This project is released under the [MIT License](/Users/wangkq/work/mlx-code/codex-responses-bridge/LICENSE).

## Repo layout

```text
.
├── LICENSE
├── README.md
├── README.en.md
├── configs/
│   └── services.example.yaml
├── docs/
├── pyproject.toml
├── scripts/
│   ├── bootstrap.sh
│   └── start.sh
└── src/
```

## Quick start

### 1. Bootstrap

```bash
./scripts/bootstrap.sh
```

### 2. Single-service mode

```bash
export CRB_PORT=8090
export CRB_UPSTREAM_BASE_URL="https://api.deepseek.com/v1"
export CRB_UPSTREAM_MODEL="deepseek-v4-pro"
export CRB_UPSTREAM_PROVIDER="deepseek"
export CRB_UPSTREAM_API_KEY="your-key"

./scripts/start.sh
```

### 3. Multi-service config mode

```bash
export CRB_USE_CONFIG_FILE=1
export CRB_CONFIG_FILE=./configs/services.example.yaml

./scripts/start.sh
```

Environment mode can override alias mapping, for example:

```bash
export CRB_MODEL_ALIASES="GPT-5.4=glm-5.1-fp8,GPT-5.5=glm-5.1-fp8"
```

or:

```bash
export CRB_MODEL_ALIASES_JSON='{"GPT-5.4":"glm-5.1-fp8","GPT-5.5":"glm-5.1-fp8"}'
```

Notes:

- there is no universal official GPT-to-vendor one-to-one mapping across providers
- built-in defaults are recommended presets based on current public vendor model names and rough capability tiers
- client model alias resolution is case-insensitive, so `GPT-5.5` and `gpt-5.5` resolve the same way

See [docs/architecture.en.md](/Users/wangkq/work/mlx-code/codex-responses-bridge/docs/architecture.en.md).

Mapping rationale: [docs/model-mapping.zh-CN.md](/Users/wangkq/work/mlx-code/codex-responses-bridge/docs/model-mapping.zh-CN.md).

Real integration notes: [docs/validation.en.md](/Users/wangkq/work/mlx-code/codex-responses-bridge/docs/validation.en.md).

## Git-ready defaults

The repo ignore rules now exclude:

- virtualenvs, caches, build outputs
- `captures/` and `*.log`
- local `.env*` files
- local `manual_testbed/`
