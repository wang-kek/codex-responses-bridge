# codex-responses-bridge

面向 Codex `Responses API` 的轻量多上游协议桥。

## 定位

这个工程专注解决一件事：

- 接收 Codex 发来的 `/v1/responses`
- 转换为上游模型可接受的协议
- 优先支持 OpenAI-style `/v1/chat/completions`
- 为后续 Anthropic Messages 适配预留清晰扩展点

它不是一个大而全的代理平台，重点是精准、可扩展、可审计。

## 当前能力

- 目标运行环境：`Python 3.8+`
- 基于 `FastAPI + Uvicorn` 的轻量启动
- 默认支持单服务环境变量启动
- 支持通过 YAML 配置文件启动多端口、多上游服务
- YAML 支持 `defaults` 和可复用 `upstreams`，减少相同参数重复配置
- 支持同一端口下拆分文本上游和多模态上游
- 支持客户端模型名别名映射，例如把 `GPT-5.4` / `GPT-5.5` 映射到实际内部模型名
- 默认按不同厂商内置不同的 GPT 名称推荐映射，而不是所有服务共用同一默认值
- 对未知客户端模型名默认回落到当前服务的默认上游模型，避免无法路由
- 已支持 `Responses -> OpenAI Chat Completions` 请求转换
- 已支持 `OpenAI Chat -> Responses` 非流式结果转换
- 已支持 `OpenAI Chat SSE -> Responses SSE` 流式事件转换
- 已支持 provider profile 字段裁剪，用于收敛不同上游的兼容差异
- 已拆分 provider adapter 规则层，用于承接厂商特定的请求改写逻辑
- 已支持部分 provider 的请求字段自动降级，例如千问兼容模式下把不被接受的 `tool_choice=required` 自动降级为 `auto`
- `/v1/models` 会同时暴露客户端别名模型和实际上游 canonical 模型
- 内置日志初始化与协议抓取能力
- 默认中文文档，同时提供英文文档

## 开源协议

本项目采用 [MIT License](/Users/wangkq/work/mlx-code/codex-responses-bridge/LICENSE) 发布。

## 目录结构

```text
.
├── LICENSE
├── README.md
├── README.en.md
├── configs/
│   └── services.example.yaml
├── docs/
│   ├── architecture.en.md
│   └── architecture.zh-CN.md
├── pyproject.toml
├── scripts/
│   ├── bootstrap.sh
│   └── start.sh
└── src/
    └── codex_responses_bridge/
        ├── __init__.py
        ├── __main__.py
        ├── app.py
        ├── config.py
        ├── logging_utils.py
        ├── models.py
        ├── request_capture.py
        ├── translators/
        │   ├── __init__.py
        │   └── responses_openai.py
        └── upstreams/
            ├── __init__.py
            ├── anthropic.py
            ├── base.py
            └── openai.py
```

## 启动方式

### 0. 一键安装

```bash
./scripts/bootstrap.sh
```

### 1. 单服务模式

```bash
export CRB_PORT=8090
export CRB_UPSTREAM_BASE_URL="https://api.deepseek.com/v1"
export CRB_UPSTREAM_MODEL="deepseek-v4-pro"
export CRB_UPSTREAM_PROVIDER="deepseek"
export CRB_UPSTREAM_API_KEY="your-key"

./scripts/start.sh
```

### 2. 多服务配置模式

```bash
export CRB_USE_CONFIG_FILE=1
export CRB_CONFIG_FILE=./configs/services.example.yaml

./scripts/start.sh
```

当前建议只维护这一份汇总配置文件：

- [configs/services.example.yaml](/Users/wangkq/work/mlx-code/codex-responses-bridge/configs/services.example.yaml)

它已经支持：

- `defaults`: 合并公共参数，例如 `host`、`protocol_mode`
- `upstreams`: 复用上游定义，例如公共 `base_url`、`api_key_env`、默认模型
- `*_upstream_ref`: 在具体服务里引用公共上游定义

## 默认上游预设

配置模板中已预留以下 provider：

- `deepseek`
- `glm-code`
- `qwen37-token`
- `mimo`

## 模型名映射

为了兼容 Codex 客户端侧固定或习惯性的模型名，服务支持在入口先做一层模型名映射。

例如：

- DeepSeek: `GPT-5.5 -> deepseek-v4-pro`
- GLM Code: `GPT-5.5 -> glm-5.1`
- Qwen: `GPT-5.5 -> qwen3.7-max`
- MiMo: `GPT-5.5 -> mimo-v2.5-pro`

可以在环境变量模式下使用默认映射，也可以在 YAML 配置中的 `model_aliases` 为每个服务单独配置。

说明：

- 不存在跨所有厂商统一官方承认的 GPT 一一对位表
- 工程默认值采用“该厂商当前公开模型名 + 接近能力档位”的推荐预设
- 解析时对客户端模型名大小写不敏感，例如 `GPT-5.5` 与 `gpt-5.5` 会命中同一条规则

如果客户端传了未知模型名，默认策略是 `default_upstream`：

- 不报“无法识别模型”
- 直接回落到该服务当前绑定的默认上游模型

环境变量模式也支持覆盖，例如：

```bash
export CRB_MODEL_ALIASES="GPT-5.4=glm-5.1-fp8,GPT-5.5=glm-5.1-fp8,gpt-5.4=glm-5.1-fp8,gpt-5.5=glm-5.1-fp8"
```

或者：

```bash
export CRB_MODEL_ALIASES_JSON='{"GPT-5.4":"glm-5.1-fp8","GPT-5.5":"glm-5.1-fp8"}'
```

如果需要改变未知模型策略，也可以设置：

```bash
export CRB_UNKNOWN_MODEL_STRATEGY=default_upstream
```

## 下一步建议

- 为不同 provider 增加更细的 reasoning、structured output、tool calling 差异适配
- 为 Anthropic 模式补充完整适配器
- 增加端到端联调脚本和真实上游回归测试

更多设计见 [docs/architecture.zh-CN.md](/Users/wangkq/work/mlx-code/codex-responses-bridge/docs/architecture.zh-CN.md)。

映射依据见 [docs/model-mapping.zh-CN.md](/Users/wangkq/work/mlx-code/codex-responses-bridge/docs/model-mapping.zh-CN.md)。

真实联调记录见 [docs/validation.zh-CN.md](/Users/wangkq/work/mlx-code/codex-responses-bridge/docs/validation.zh-CN.md)。

## 提交建议

以下内容默认不会进入 Git：

- 本地虚拟环境、测试缓存、构建产物
- 协议抓取目录 `captures/`、日志文件 `*.log`
- 私有环境变量文件 `.env*`
- 本地手工联调目录 `manual_testbed/`
