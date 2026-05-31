# Architecture

## Goals

- translate Codex `Responses API` into upstream chat-style protocols
- keep the default setup simple
- support one text upstream and one multimodal upstream on the same port
- keep optional request capture for troubleshooting

## Runtime modes

### Single-service mode

- pass the key inline on the command line
- run `./scripts/start-zhipu.sh` / `./scripts/start-deepseek.sh` / `./scripts/start-deepseek-local.sh` / `./scripts/start-qwen.sh` / `./scripts/start-mimo.sh`

### Multi-service mode

- put keys in `configs/model-keys.env`
- edit `configs/services.example.yaml`
- run `./scripts/start-all.sh`

## Main modules

- `config.py`: loads environment variables and flat YAML service configs
- `provider_profiles.py`: removes fields that some providers do not accept
- `provider_adapters.py`: applies provider-specific compatibility rewrites
- `app.py`: FastAPI routes for `/health`, `/v1/models`, `/v1/responses`
- `translators/responses_openai.py`: request and response translation
- `upstreams/openai.py`: upstream HTTP transport
- `request_capture.py`: optional protocol capture

## Local Upstreams

When an upstream URL points to `127.0.0.1`, `localhost`, or `::1`, the bridge bypasses proxy environment variables and connects directly to the local service. This prevents local model servers from being accidentally routed through HTTP/HTTPS proxies.

The default local DeepSeek route is:

- URL: `http://127.0.0.1:8000/v1`
- model: `deepseek-v4-pro`
- port: `8096`
- API key: not required

## Codex Tool History Guards

During long tasks, Codex Desktop may send previous tool calls and tool outputs back to `/v1/responses`. Native Codex models can usually handle this history, but many OpenAI Chat-compatible upstreams reject it when the payload is too large or a historical tool argument is incomplete.

The bridge applies shared guards in `provider_adapters.py`:

- Inline base64 images inside `tool` messages are replaced with short summaries, for example screenshot results returned as `data:image/png;base64,...`.
- Historical `tool_calls.function.arguments` values that are not valid JSON are wrapped into valid JSON with the parse error and a raw preview.
- Requests without `max_tokens` or `max_completion_tokens` get `max_tokens=4096` by default.
- For Qwen long tool loops, tools stay enabled; only old tool history is compacted.

These guards have been verified on both local GLM and Zhipu public `glm-code` routes. The goal is to keep Codex tool loops running instead of disabling tool calls.
