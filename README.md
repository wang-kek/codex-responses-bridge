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

本地 GLM 如果运行在 `http://192.168.1.232:8000/v1`，默认走 `glm-5.1-fp8`，并且支持多模态上游：

```bash
LOCAL_GLM_API_KEY=你的本地key LOCAL_VLM_API_KEY=你的多模态key ./scripts/start-glm-local.sh
```

本地 DeepSeek 如果运行在 `http://127.0.0.1:8000/v1`，默认走 `deepseek-v4-flash`。如果你的本地服务不需要鉴权，可以直接启动：

```bash
./scripts/start-deepseek-local.sh
```

如果本地服务也要求 key，可以这样启动：

```bash
DEEPSEEK_LOCAL_API_KEY=你的本地key ./scripts/start-deepseek-local.sh
```

默认还会带上一个多模态上游：

- 地址：`http://192.168.1.251:33338/v1`
- 模型：`Qwen/Qwen3-VL-8B-Instruct`
- key：`LOCAL_VLM_API_KEY`

也就是说，DeepSeek 负责文本，图片输入会自动切到这个多模态上游。

如果你想改端口，也可以直接叠加：

```bash
ZHIPU_API_KEY=你的key PORT=8082 ./scripts/start-zhipu.sh
```

启动后，默认监听 `0.0.0.0`。

## 多模型启动

把多个模型都起起来时，用这个文件集中放 key：

[configs/model-keys.env.example](configs/model-keys.env.example)

复制成 `configs/model-keys.env`，填这些即可：

- `ZHIPU_API_KEY`
- `DEEPSEEK_API_KEY`
- `DEEPSEEK_LOCAL_API_KEY`
- `DASHSCOPE_API_KEY`
- `MIMO_API_KEY`
- `LOCAL_GLM_API_KEY`
- `LOCAL_VLM_API_KEY`

然后启动：

```bash
./scripts/start-all.sh
```

如果要后台运行：

```bash
./scripts/start-all.sh --daemon
```

停止全部服务：

```bash
./scripts/stop-all.sh
```

查看状态：

```bash
./scripts/status-all.sh
```

多端口配置在这里：

[configs/services.yaml](configs/services.yaml)

每个服务都可以单独用 `enabled: true/false` 控制是否启动；设成 `false` 后，这个服务会被直接跳过，对应端口也不会建立。`./scripts/start-all.sh` 默认优先读取 `configs/services.yaml`。

默认端口对应关系：

- `8080` -> 本地 GLM，`glm-5.1-fp8`，支持 `LOCAL_GLM_API_KEY` 和 `LOCAL_VLM_API_KEY`
- `8081` -> 本地 DeepSeek，`deepseek-v4-flash`，默认可无 key，也支持 `DEEPSEEK_LOCAL_API_KEY`
- `8082` -> 智谱公网
- `8083` -> DeepSeek 公网，文本走 DeepSeek，多模态走 `Qwen/Qwen3-VL-8B-Instruct`
- `8084` -> 通义千问
- `8085` -> 小米 MiMo

Codex 客户端里填写：

- 本地 GLM：`http://你的机器IP:8080/v1`
- 本地 DeepSeek：`http://你的机器IP:8081/v1`
- 智谱公网：`http://你的机器IP:8082/v1`
- DeepSeek：`http://你的机器IP:8083/v1`
- 通义千问：`http://你的机器IP:8084/v1`
- 小米 MiMo：`http://你的机器IP:8085/v1`

API Key 可以填任意非空字符串，真正访问上游用的是 `configs/model-keys.env` 里的 key。

## Key 配置规则

上游鉴权支持两种写法：

- `api_key_env: SOME_KEY`：从环境变量或 `configs/model-keys.env` 读取。
- `api_key: your-key`：直接写在 YAML 中，优先级高于 `api_key_env`。

如果确实是无鉴权本地服务，可以把 `api_key_env` 写成空字符串 `""`。不建议把公网 key 写进 YAML，避免误提交。

多模态上游也一样，例如 `LOCAL_VLM_API_KEY` 会被 `multimodal_api_key_env: LOCAL_VLM_API_KEY` 使用。

## 验证服务

启动后可以先检查健康状态：

```bash
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8081/health
curl http://127.0.0.1:8082/health
curl http://127.0.0.1:8083/health
curl http://127.0.0.1:8084/health
curl http://127.0.0.1:8085/health
```

也可以查看暴露给 Codex 的模型名：

```bash
curl http://127.0.0.1:8080/v1/models
```

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

## 多模态现状

- 本地 GLM 默认带多模态上游适配。
- DeepSeek 本地和 DeepSeek 公网本身仍然只负责文本，但默认也都挂了一个独立多模态上游。
- 当前默认多模态上游地址是 `http://192.168.1.251:33338/v1`，模型是 `Qwen/Qwen3-VL-8B-Instruct`，通过 `LOCAL_VLM_API_KEY` 鉴权。

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

## 变更记录

见 [CHANGELOG.md](CHANGELOG.md)。

## 打包发布

macOS 下需使用 `gtar`（GNU tar）打包，避免 `._` 扩展属性和 xattr 残留。可通过 `brew install gnu-tar` 安装。

```bash
gtar czf ../codex-responses-bridge-linux-release-$(date +%Y%m%d-%H%M%S).tar.gz \
  --exclude='._*' --exclude='.DS_Store' --exclude='.git' \
  --exclude='.venv' --exclude='__pycache__' --exclude='*.egg-info' \
  --exclude='configs/services.yaml' --exclude='configs/model-keys.env' \
  --no-xattrs --owner=0 --group=0 --numeric-owner \
  -C .. codex-responses-bridge
```

## 开源协议

本项目采用 [MIT License](LICENSE)。
