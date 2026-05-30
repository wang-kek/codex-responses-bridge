# 模型名映射说明

本文记录 bridge 内置的“客户端 GPT 名称 -> 上游厂商模型名”默认映射策略。

## 设计原则

- 不存在所有厂商共同承认的官方“一对一 GPT 等价模型名”
- bridge 的默认值采用“厂商当前公开模型名 + 能力层级接近”的推荐映射
- 用户仍然可以在 `model_aliases` 中按自己的评测结果覆盖
- 未命中的客户端模型名默认按 `unknown_model_strategy=default_upstream` 回落到该服务的 canonical 模型

## 2026-05-30 当前预设

### DeepSeek

- `GPT-5.5 -> deepseek-v4-pro`
- `GPT-5.4 -> deepseek-v4-pro`
- `GPT-5.4-mini -> deepseek-v4-flash`
- `GPT-4.1 -> deepseek-v4-flash`
- `GPT-4.1-mini -> deepseek-v4-flash`
- `o4-mini -> deepseek-v4-flash`

依据：

- DeepSeek 官方模型接口：`GET /v1/models`
- 当前工程默认按高档位与轻量档位做两档推荐

### 智谱 GLM Code

- `GPT-5.5 -> glm-5.1`
- `GPT-5.4 -> glm-5-turbo`
- `GPT-5.4-mini -> glm-4.6`
- `GPT-4.1 -> glm-4.7`
- `GPT-4.1-mini -> glm-4.6`
- `o4-mini -> glm-5-turbo`

依据：

- 智谱 Coding PaaS 官方模型接口：`GET /models`
- `glm-5.1` 适合作为高档位默认值，`glm-5-turbo` 适合作为更便宜一档

### 通义千问 Qwen

- `GPT-5.5 -> qwen3.7-max`
- `GPT-5.4 -> qwen3.7-max`
- `GPT-5.4-mini -> qwen3.6-flash`
- `GPT-4.1 -> qwen3.6-plus`
- `GPT-4.1-mini -> qwen3.6-flash`
- `o4-mini -> qwen3.6-flash`

依据：

- 阿里云百炼官方迁移文档给出 OpenAI 到 Qwen 的推荐关系：
- `GPT-5.5 -> qwen3.7-max`
- `GPT-5.4 -> qwen3.7-max`
- `GPT-5.4-mini -> qwen3.6-flash`

说明：

- `GPT-4.1`、`GPT-4.1-mini`、`o4-mini` 不是百炼官方逐条给出的对位名
- 这里按同一能力档位做推荐映射，属于工程默认值，不是厂商官方等价声明

### 小米 MiMo

- `GPT-5.5 -> mimo-v2.5-pro`
- `GPT-5.4 -> mimo-v2.5-pro`
- `GPT-5.4-mini -> mimo-v2-flash`
- `GPT-4.1 -> mimo-v2-pro`
- `GPT-4.1-mini -> mimo-v2-flash`
- `o4-mini -> mimo-v2-flash`

依据：

- MiMo 官方模型接口：`GET /v1/models`
- 当前文本模型可以理解为 `flash / pro / 2.5-pro` 三档

说明：

- MiMo 官方当前公开的是自有模型名，不提供 GPT 对位表
- 所以上述映射同样属于推荐值，建议结合延迟、成本、代码任务表现继续微调

## 为什么有些映射只能叫“推荐值”

- Qwen 有官方迁移表，所以优先按官方表
- DeepSeek、GLM、MiMo 更常见的是官方模型列表，不是官方 GPT 对位表
- 所以这些厂商的默认映射是工程推荐值，不是厂商官方等价声明

## 覆盖方式

可以通过 YAML 为单个服务覆盖：

```yaml
services:
  - name: glm-code-main
    port: 8091
    provider: glm-code
    base_url: https://open.bigmodel.cn/api/coding/paas/v4
    api_key_env: ZHIPU_API_KEY
    model: glm-5.1
    model_aliases:
      GPT-5.4: glm-5.1
      GPT-5.5: glm-5.1
```

也可以通过环境变量覆盖：

```bash
export CRB_MODEL_ALIASES="GPT-5.4=glm-5.1,GPT-5.5=glm-5.1"
```
