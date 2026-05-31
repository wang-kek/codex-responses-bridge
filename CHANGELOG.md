# Changelog

## 0.1.0 - 2026-05-31

首个可用版本，目标是把 Codex Desktop / Codex CLI 的 `/v1/responses` 请求稳定转换到常见 OpenAI Chat 兼容上游。

### 启动体验

- 提供单模型一行启动脚本：
  - `scripts/start-zhipu.sh`
  - `scripts/start-deepseek.sh`
  - `scripts/start-deepseek-local.sh`
  - `scripts/start-qwen.sh`
  - `scripts/start-mimo.sh`
- 提供多模型集中启动脚本：`scripts/start-all.sh`。
- 多模型 key 统一放在 `configs/model-keys.env`，仓库只提交 `configs/model-keys.env.example`。
- 首次启动自动创建 `.venv`、升级 `pip` 并安装当前项目，不再需要单独执行 bootstrap。

### 协议转换

- 支持 Codex `/v1/responses` 到 `/v1/chat/completions` 的请求转换。
- 支持流式响应转换回 Responses API SSE 事件。
- 支持 `/health` 和 `/v1/models`。
- 支持文本上游和可选多模态上游分流。
- 本地 loopback 上游自动绕过系统代理环境变量，避免 `127.0.0.1` 服务被错误转发到 HTTP/HTTPS 代理。

### 厂商默认配置

- 智谱公网 Coding PaaS：`glm-code`，默认模型 `glm-5.1`。
- DeepSeek：默认模型 `deepseek-v4-pro`。
- 本地 DeepSeek：默认地址 `http://127.0.0.1:8000/v1`，无需 key。
- 通义千问 DashScope 兼容模式：默认模型 `qwen3.7-max`。
- 小米 MiMo：默认模型 `mimo-v2.5-pro`。

### 模型名映射

- 内置 GPT 风格模型名到厂商模型名的默认映射。
- 未识别模型名默认回落到当前服务配置的 `model`。
- 支持通过 `model_aliases` 覆盖单个服务的映射规则。

### Codex 工具历史保护

- 压缩工具结果中的内联 base64 图片，避免截图历史撑爆文本模型上下文。
- 修复历史 `tool_calls.function.arguments` 中不完整 JSON，避免上游返回 `Unterminated string`。
- 请求没有指定输出上限时默认补 `max_tokens=4096`。
- Qwen 长工具循环时保留工具能力，只压缩历史工具消息，避免模型继续陷入失败循环。

### 文档和发布

- 默认文档语言为中文，并提供英文 README 和架构说明。
- 删除复杂验证文档，保留更适合新手使用的启动说明。
- 使用 MIT License 发布。
