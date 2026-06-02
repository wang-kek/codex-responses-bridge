# 架构设计

## 设计目标

- 把 Codex `Responses API` 转成上游常见的 chat 风格协议
- 默认用法尽量简单
- 同一个端口可以同时挂文本上游和多模态上游
- 保留可选抓包能力，便于排查问题

## 运行模式

### 单服务模式

- 一行命令传 key
- 执行 `./scripts/start-glm-local.sh` / `./scripts/start-zhipu.sh` / `./scripts/start-deepseek.sh` / `./scripts/start-deepseek-local.sh` / `./scripts/start-qwen.sh` / `./scripts/start-mimo.sh`

### 多服务模式

- 把 key 写入 `configs/model-keys.env`
- 改 `configs/services.example.yaml`
- 执行 `./scripts/start-all.sh`

## 核心模块

- `config.py`: 负责加载环境变量和扁平 YAML 配置
- `provider_profiles.py`: 负责移除部分厂商不接受的字段
- `provider_adapters.py`: 负责厂商特定兼容改写
- `app.py`: 提供 `/health`、`/v1/models`、`/v1/responses`
- `translators/responses_openai.py`: 负责请求和响应转换
- `upstreams/openai.py`: 负责上游 HTTP 转发
- `request_capture.py`: 负责可选抓包

## 本地上游

如果上游地址是 `127.0.0.1`、`localhost` 或 `::1`，bridge 会自动绕过系统代理环境变量，直接访问本机服务。这是为了避免本地模型服务被错误转发到 HTTP/HTTPS 代理。

本地 DeepSeek 默认配置为：

- 地址：`http://127.0.0.1:8000/v1`
- 模型：`deepseek-v4-flash`
- 端口：`8081`
- API key：默认可不填；如果本地服务要求鉴权，可以使用 `DEEPSEEK_LOCAL_API_KEY`

本地 GLM 默认配置为：

- 地址：`http://192.168.1.232:8000/v1`
- 模型：`glm-5.1-fp8`
- 端口：`8080`
- 文本 key：`LOCAL_GLM_API_KEY`
- 多模态 key：`LOCAL_VLM_API_KEY`

本地 DeepSeek 默认也带同一个多模态上游：

- 地址：`http://192.168.1.251:33338/v1`
- 模型：`Qwen/Qwen3-VL-8B-Instruct`
- 端口：`8081` 或 `8083`
- key：`LOCAL_VLM_API_KEY`

也就是说，DeepSeek 只负责文本，上游图片输入会自动切到独立的多模态服务。若某个本地服务明确无鉴权，可在 YAML 中设置 `api_key_env: ""`。

## Codex 工具历史保护

长时间任务中，Codex 桌面版会把历史工具调用和工具输出重新提交给 `/v1/responses`。这些历史对原生 Codex 模型通常可接受，但部分 OpenAI Chat 兼容上游会因为上下文过大或历史参数格式不完整而拒绝请求。

bridge 在 `provider_adapters.py` 中做统一保护：

- `tool` 消息中的内联 base64 图片会被替换成摘要，例如截图工具返回的 `data:image/png;base64,...`。
- 历史 `tool_calls.function.arguments` 如果不是合法 JSON，会被包装成合法 JSON，并保留错误信息和原始片段预览。
- 请求未指定 `max_tokens` 或 `max_completion_tokens` 时，默认补 `max_tokens=4096`。
- Qwen 在长工具循环后仍会保留 tools 能力，只压缩历史工具消息，避免模型陷入重复失败。

这些保护在本地 GLM 和智谱公网 `glm-code` 链路上都已验证，目标是让 Codex 的工具循环继续执行，而不是关闭工具调用。
