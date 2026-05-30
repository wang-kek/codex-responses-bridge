# codex-responses-bridge

把 Codex 的 `/v1/responses` 转成常见大模型厂商可接受的 `/v1/chat/completions`。

这个工程优先解决“简单、直接、能跑起来”。

## 最简单的用法

### 1. 安装

```bash
./scripts/bootstrap.sh
```

### 2. 填 `.env`

把 [.env.example](.env.example) 复制成 `.env`，只改这 5 个字段：

- `PORT`
- `PROVIDER`
- `BASE_URL`
- `API_KEY`
- `MODEL`

### 3. 启动

```bash
./scripts/start.sh
```

默认监听地址是 `0.0.0.0`，更适合内网发布和联调。

## 多端口启动

如果你要同时起多个端口，就改这个文件。这个示例已经对齐了当前验证通过的默认测试环境：

[configs/services.example.yaml](configs/services.example.yaml)

这个配置已经是扁平格式了，每个服务只需要这些直白字段：
- `port`
- `provider`
- `base_url`
- `api_key_env`
- `api_key`
- `model`

也支持两种填 key 的方式：

- 写 `api_key_env`：适合把 key 放环境变量
- 写 `api_key`：适合直接复制配置后马上测试

如果同一个端口还要接多模态，再补：

- `multimodal_provider`
- `multimodal_base_url`
- `multimodal_api_key_env`
- `multimodal_model`

启动命令：

```bash
./scripts/start-config.sh
```

## 当前支持

- Python `3.8+`
- 单服务快速启动
- 多端口配置启动
- 文本与多模态分流
- GPT 风格模型名自动映射
- 未识别模型名自动回落到当前服务默认模型
- Codex 工具历史保护
- 可选抓包日志

## Codex 工具历史保护

Codex 桌面版在长任务里会把工具调用历史一起发回来。bridge 会在转发给上游前做几类安全改写，避免兼容 OpenAI Chat 的厂商服务直接拒绝请求：

- 工具结果里的 `data:image/...;base64,...` 会被替换成简短摘要，避免截图历史把文本模型上下文撑爆。
- 历史 `tool_calls.function.arguments` 如果已经是不完整 JSON，会被包装成合法 JSON，避免上游报 `Unterminated string`。
- 客户端没有传输出上限时，会默认补 `max_tokens=4096`，避免部分兼容服务把缺省值理解成 `0 output tokens`。

这些保护不会关闭工具调用，也不会改用户消息里的真实多模态输入；只处理 Codex 工具历史回灌中容易导致上游报错的内容。

## GPT 名称映射

客户端常见会传这些名字：

- `GPT-5.5`
- `GPT-5.4`
- `GPT-5.4-mini`
- `GPT-4.1`
- `GPT-4.1-mini`
- `o4-mini`

bridge 会先把这些名称映射到上游厂商模型名。

映射规则文档：

[docs/model-mapping.zh-CN.md](docs/model-mapping.zh-CN.md)

映射原则：

- 有官方迁移表的，按官方迁移表
- 没有官方迁移表的，按当前模型档位给推荐值
- 传了不认识的名称时，默认回落到当前服务的 `model`

## 默认厂商标识

- `deepseek`
- `glm-code`
- `qwen37-token`
- `mimo`

## 仓库结构

```text
.
├── .env.example
├── LICENSE
├── README.md
├── README.en.md
├── configs/
│   └── services.example.yaml
├── docs/
│   ├── architecture.en.md
│   ├── architecture.zh-CN.md
│   └── model-mapping.zh-CN.md
├── scripts/
│   ├── bootstrap.sh
│   ├── start.sh
│   └── start-config.sh
└── src/
```

## 开源协议

本项目采用 [MIT License](LICENSE)。
