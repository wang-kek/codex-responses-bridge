# codex-responses-bridge

把 Codex 的 `/v1/responses` 转成常见大模型厂商可接受的 `/v1/chat/completions`。

目标很直接：新手能复制、填 key、启动就跑。

## 单模型启动

最简单的方式是一行命令。

```bash
ZHIPU_API_KEY=你的key ./scripts/start-zhipu.sh
```

其他厂商也一样：

```bash
DEEPSEEK_API_KEY=你的key ./scripts/start-deepseek.sh
DASHSCOPE_API_KEY=你的key ./scripts/start-qwen.sh
MIMO_API_KEY=你的key ./scripts/start-mimo.sh
```

如果你想改端口，也可以直接叠加：

```bash
ZHIPU_API_KEY=你的key PORT=8092 ./scripts/start-zhipu.sh
```

启动后，默认监听 `0.0.0.0`。

## 多模型启动

把多个模型都起起来时，用这个文件集中放 key：

[configs/model-keys.env.example](configs/model-keys.env.example)

复制成 `configs/model-keys.env`，填这些即可：

- `ZHIPU_API_KEY`
- `DEEPSEEK_API_KEY`
- `DASHSCOPE_API_KEY`
- `MIMO_API_KEY`

然后启动：

```bash
./scripts/start-all.sh
```

多端口配置在这里：

[configs/services.example.yaml](configs/services.example.yaml)

默认端口对应关系：

- `8092` -> 智谱公网
- `8093` -> DeepSeek
- `8094` -> 通义千问
- `8095` -> 小米 MiMo

## 当前支持

- Python `3.8+`
- 单模型一行启动
- 多模型集中启动
- 文本与多模态分流
- GPT 风格模型名自动映射
- 未识别模型名自动回落到当前服务默认模型
- Codex 工具历史保护
- 可选抓包日志

## Codex 工具历史保护

Codex 桌面版在长任务里会把工具调用历史一起发回来。bridge 会在转发给上游前做几类安全改写：

- 工具结果里的 `data:image/...;base64,...` 会被替换成简短摘要。
- 历史 `tool_calls.function.arguments` 如果已经是不完整 JSON，会被包装成合法 JSON。
- 客户端没有传输出上限时，会默认补 `max_tokens=4096`。

这些保护不会关闭工具调用，也不会改用户消息里的真实多模态输入。

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

## 仓库结构

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
│   ├── start-mimo.sh
│   ├── start-qwen.sh
│   ├── start.sh
│   └── start-zhipu.sh
└── src/
```

## 开源协议

本项目采用 [MIT License](LICENSE)。
