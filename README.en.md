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

If local DeepSeek is running at `http://127.0.0.1:8000`, no key is needed. It defaults to `deepseek-v4-flash`:

```bash
./scripts/start-deepseek-local.sh
```

You can also override the port inline:

```bash
ZHIPU_API_KEY=your-key PORT=8092 ./scripts/start-zhipu.sh
```

Default host is `0.0.0.0`.

## Multi-model startup

Put all keys in one visible file:

[configs/model-keys.env.example](configs/model-keys.env.example)

Copy it to `configs/model-keys.env` and fill:

- `ZHIPU_API_KEY`
- `DEEPSEEK_API_KEY`
- `DASHSCOPE_API_KEY`
- `MIMO_API_KEY`

Then run:

```bash
./scripts/start-all.sh
```

Multi-port service definitions live in:

[configs/services.example.yaml](configs/services.example.yaml)

Default port map:

- `8092` -> Zhipu public
- `8093` -> DeepSeek
- `8094` -> Qwen
- `8095` -> MiMo
- `8096` -> local DeepSeek, `deepseek-v4-flash`, no key required

Use these Base URLs in Codex:

- Zhipu public: `http://your-host-ip:8092/v1`
- DeepSeek: `http://your-host-ip:8093/v1`
- Qwen: `http://your-host-ip:8094/v1`
- MiMo: `http://your-host-ip:8095/v1`
- local DeepSeek: `http://your-host-ip:8096/v1`

The Codex client API key can be any non-empty string. Upstream keys come from `configs/model-keys.env`.

## Check Services

After startup, check health:

```bash
curl http://127.0.0.1:8092/health
curl http://127.0.0.1:8093/health
curl http://127.0.0.1:8094/health
curl http://127.0.0.1:8095/health
curl http://127.0.0.1:8096/health
```

List models exposed to Codex:

```bash
curl http://127.0.0.1:8092/v1/models
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
│   ├── start-deepseek.sh
│   ├── start-deepseek-local.sh
│   ├── start-mimo.sh
│   ├── start-qwen.sh
│   ├── start.sh
│   └── start-zhipu.sh
└── src/
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md).

## License

MIT. See [LICENSE](LICENSE).
