# codex-responses-bridge

Translate Codex `/v1/responses` into upstream `/v1/chat/completions`.

The goal is simple: copy, fill keys, run.

## Single-model startup

The easiest way is a one-line command.

```bash
ZHIPU_API_KEY=your-key ./scripts/start-zhipu.sh
```

Other providers work the same way:

```bash
DEEPSEEK_API_KEY=your-key ./scripts/start-deepseek.sh
DASHSCOPE_API_KEY=your-key ./scripts/start-qwen.sh
MIMO_API_KEY=your-key ./scripts/start-mimo.sh
```

If local GLM is running at `http://192.168.1.232:8000/v1`, it defaults to `glm-5.1-fp8` and supports a multimodal upstream:

```bash
LOCAL_GLM_API_KEY=your-local-key LOCAL_VLM_API_KEY=your-mm-key ./scripts/start-glm-local.sh
```

If local DeepSeek is running at `http://127.0.0.1:8000/v1`, it defaults to `deepseek-v4-flash`. If your local service does not require auth, run:

```bash
./scripts/start-deepseek-local.sh
```

If your local service requires a key, run:

```bash
DEEPSEEK_LOCAL_API_KEY=your-local-key ./scripts/start-deepseek-local.sh
```

By default it also carries a multimodal upstream:

- URL: `http://192.168.1.251:33338/v1`
- model: `Qwen/Qwen3-VL-8B-Instruct`
- key: `LOCAL_VLM_API_KEY`

So DeepSeek handles text, while image input is routed to that multimodal upstream.

You can also override the port inline:

```bash
ZHIPU_API_KEY=your-key PORT=8082 ./scripts/start-zhipu.sh
```

Default host is `0.0.0.0`.

## Multi-model startup

Put all keys in one visible file:

[configs/model-keys.env.example](configs/model-keys.env.example)

Copy it to `configs/model-keys.env` and fill:

- `ZHIPU_API_KEY`
- `DEEPSEEK_API_KEY`
- `DEEPSEEK_LOCAL_API_KEY`
- `DASHSCOPE_API_KEY`
- `MIMO_API_KEY`
- `LOCAL_GLM_API_KEY`
- `LOCAL_VLM_API_KEY`

Then run:

```bash
./scripts/start-all.sh
```

To run in the background:

```bash
./scripts/start-all.sh --daemon
```

Stop all services:

```bash
./scripts/stop-all.sh
```

Check status:

```bash
./scripts/status-all.sh
```

Multi-port service definitions live in:

[configs/services.yaml](configs/services.yaml)

Each service can be controlled independently with `enabled: true/false`; when set to `false`, the service is skipped and its port is never bound. `./scripts/start-all.sh` now prefers `configs/services.yaml`.

Default port map:

- `8080` -> local GLM, `glm-5.1-fp8`, supports `LOCAL_GLM_API_KEY` and `LOCAL_VLM_API_KEY`
- `8081` -> local DeepSeek, `deepseek-v4-flash`, key optional via `DEEPSEEK_LOCAL_API_KEY`
- `8082` -> Zhipu public
- `8083` -> DeepSeek public, text via DeepSeek and multimodal via `Qwen/Qwen3-VL-8B-Instruct`
- `8084` -> Qwen
- `8085` -> MiMo

Use these Base URLs in Codex:

- local GLM: `http://your-host-ip:8080/v1`
- local DeepSeek: `http://your-host-ip:8081/v1`
- Zhipu public: `http://your-host-ip:8082/v1`
- DeepSeek public: `http://your-host-ip:8083/v1`
- Qwen: `http://your-host-ip:8084/v1`
- MiMo: `http://your-host-ip:8085/v1`

The Codex client API key can be any non-empty string. Upstream keys come from `configs/model-keys.env`.

## Key Rules

Upstream auth supports two forms:

- `api_key_env: SOME_KEY`: read the key from an environment variable or `configs/model-keys.env`.
- `api_key: your-key`: put the key directly in YAML. This takes precedence over `api_key_env`.

For a truly keyless local service, set `api_key_env: ""`. Do not put public cloud keys directly in YAML if the file may be committed.

Multimodal upstreams follow the same rule. For example, `LOCAL_VLM_API_KEY` is used by `multimodal_api_key_env: LOCAL_VLM_API_KEY`.

## Check Services

After startup, check health:

```bash
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8081/health
curl http://127.0.0.1:8082/health
curl http://127.0.0.1:8083/health
curl http://127.0.0.1:8084/health
curl http://127.0.0.1:8085/health
```

List models exposed to Codex:

```bash
curl http://127.0.0.1:8080/v1/models
```

## Supported

- Python `3.8+`
- One-line single-model startup
- Multi-model startup from one visible config file
- text and multimodal routing
- GPT-style model name mapping
- fallback to the service default model for unknown names
- Codex tool-history guards
- optional request capture

## Codex tool-history guards

During long tasks, Codex Desktop may send previous tool history back to the model. Before forwarding upstream, the bridge applies a few safe guards:

- Inline `data:image/...;base64,...` tool outputs are replaced with short summaries.
- Historical `tool_calls.function.arguments` values that are not valid JSON are wrapped into valid JSON.
- If the client does not send an output limit, the bridge adds `max_tokens=4096`.

These guards do not disable tool calls or alter real multimodal user input.

## Model mapping

See:

[docs/model-mapping.zh-CN.md](docs/model-mapping.zh-CN.md)

## Multimodal status

- Local GLM ships with a multimodal upstream by default.
- Local DeepSeek and public DeepSeek still use DeepSeek only for text, but both now attach an independent multimodal upstream.
- The default multimodal upstream is `http://192.168.1.251:33338/v1` with model `Qwen/Qwen3-VL-8B-Instruct`, authenticated by `LOCAL_VLM_API_KEY`.

## Repository layout

```text
.
├── LICENSE
├── README.md
├── README.en.md
├── configs/
│   ├── model-keys.env.example
│   └── services.example.yaml
├── docs/
│   ├── architecture.en.md
│   ├── architecture.zh-CN.md
│   └── model-mapping.zh-CN.md
├── scripts/
│   ├── start-all.sh
│   ├── start-glm-local.sh
│   ├── start-deepseek.sh
│   ├── start-deepseek-local.sh
│   ├── start-mimo.sh
│   ├── start-qwen.sh
│   ├── start.sh
│   ├── start-zhipu.sh
│   ├── stop-all.sh
│   └── status-all.sh
└── src/
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## Release Packaging

On macOS, use `gtar` (GNU tar) to avoid `._` extended attributes and xattr metadata. Install via `brew install gnu-tar`.

```bash
gtar czf ../codex-responses-bridge-linux-release-$(date +%Y%m%d-%H%M%S).tar.gz \
  --exclude='._*' --exclude='.DS_Store' --exclude='.git' \
  --exclude='.venv' --exclude='__pycache__' --exclude='*.egg-info' \
  --exclude='configs/services.yaml' --exclude='configs/model-keys.env' \
  --no-xattrs --owner=0 --group=0 --numeric-owner \
  -C .. codex-responses-bridge
```

## License

MIT. See [LICENSE](LICENSE).
