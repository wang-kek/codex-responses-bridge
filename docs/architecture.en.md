# Architecture

## Goals

- precisely bridge Codex `Responses API` to multiple upstream protocols
- focus on OpenAI-style chat upstreams first
- keep a clean future path for Anthropic support
- allow one local port to route to separate text and multimodal upstreams
- keep strong observability through logs and protocol capture

## Runtime modes

- Single-service mode from environment variables
- Multi-service mode from a YAML config file

## Main modules

- `config.py`: config loading and normalization
- `config.py`: model alias mapping from client-visible names to upstream names
- `config.py`: env override support via `CRB_MODEL_ALIASES` and `CRB_MODEL_ALIASES_JSON`
- `provider_profiles.py`: provider capability profiles and generic field sanitization
- `provider_adapters.py`: provider-specific request rewrite rules before upstream dispatch
- `app.py`: FastAPI app and routes
- `translators/responses_openai.py`: request mapping, non-stream translation, and SSE translation
- `upstreams/openai.py`: upstream transport
- `request_capture.py`: protocol capture for debugging and testing
