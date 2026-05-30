# codex-responses-bridge

A simple bridge from Codex `/v1/responses` to upstream `/v1/chat/completions`.

## Quick start

### 1. Bootstrap

```bash
./scripts/bootstrap.sh
```

### 2. Edit `.env`

Copy [.env.example](.env.example) to `.env`, then update:

- `PORT`
- `PROVIDER`
- `BASE_URL`
- `API_KEY`
- `MODEL`

### 3. Start

```bash
./scripts/start.sh
```

Default host is `0.0.0.0`.

## Multi-port mode

Edit:

[configs/services.example.yaml](configs/services.example.yaml)

This example mirrors the validated default test environment.

Each service entry can use either `api_key_env` or direct `api_key`.

Then run:

```bash
./scripts/start-config.sh
```

## Codex Tool History Guards

Codex Desktop may send previous tool-call history back to the model during long tasks. Before forwarding a request upstream, the bridge applies a few safe guards:

- Inline `data:image/...;base64,...` images inside tool outputs are replaced with short summaries so screenshots do not overflow text-model context windows.
- Invalid historical `tool_calls.function.arguments` strings are wrapped into valid JSON so upstream services do not reject the whole request with `Unterminated string`.
- If the client does not send an output limit, the bridge adds `max_tokens=4096` by default.

These guards do not disable tool calls and do not alter real multimodal user input. They only clean up tool-history payloads that common OpenAI-compatible upstreams may reject.

## Model mapping

See:

[docs/model-mapping.zh-CN.md](docs/model-mapping.zh-CN.md)

Rules:

- use official migration mapping if a vendor provides one
- otherwise use same-tier recommended defaults
- unknown client names fall back to the service default `model`

## License

MIT. See [LICENSE](LICENSE).
