# 验证记录

本文档记录 `codex-responses-bridge` 针对已验证上游的真实联调结果。

更新时间：2026-05-30

## 验证范围

- 本地智谱文本模型
- 本地多模态模型
- 智谱公网 `coder plan`
- DeepSeek 公网
- 小米 MiMo 公网
- 阿里云百炼千问兼容模式

所有验证均基于 bridge 当前实现的 OpenAI-style 上游适配能力完成。

## 1. 本地智谱文本模型

### 上游信息

- URL: `http://192.168.1.232:8000/v1`
- 模型: `glm-5.1-fp8`
- 路径:
  - `/v1/models`
  - `/v1/chat/completions`

### 上游直连结论

- `GET /v1/models` 正常，模型 `glm-5.1-fp8` 可见。
- 非流式文本请求成功。
- 流式 reasoning 增量成功，字段名为 `reasoning`。
- function tool call 成功。

### bridge 验证结论

验证模式：

- 单服务环境变量模式
- 配置文件模式

已通过项：

- `GET /health`
- `GET /v1/models`
- `/v1/responses` 非流式文本
- `/v1/responses` 非流式 tool call
- `/v1/responses` 非流式 function_call_output 跟进
- `/v1/responses` 流式 reasoning 事件
- `/v1/responses` 流式 output_text 事件
- `/v1/responses` 流式 function_call_arguments 事件

### 重要说明

环境变量模式下，如果不覆盖默认 alias，`GPT-5.4` / `GPT-5.5` 会默认映射到 `GLM-5.1`，而不是本地实际可用的 `glm-5.1-fp8`。因此本地部署时应显式配置：

```bash
CRB_MODEL_ALIASES='GPT-5.4=glm-5.1-fp8,GPT-5.5=glm-5.1-fp8,gpt-5.4=glm-5.1-fp8,gpt-5.5=glm-5.1-fp8'
```

## 2. 本地多模态模型

### 上游信息

- URL: `http://192.168.1.251:33338/v1`
- 模型: `Qwen/Qwen3-VL-8B-Instruct`
- 路径:
  - `/v1/models`
  - `/v1/chat/completions`

### 上游直连结论

- `GET /v1/models` 正常。
- 带 `image_url` 的 OpenAI-style 多模态请求成功。
- 使用 1x1 PNG 的 `data:` URL 图片输入，模型能正确回答“图片为空白”。

### bridge 验证结论

部署方式：

- 同一端口绑定文本上游 `glm-5.1-fp8`
- 多模态上游绑定 `Qwen/Qwen3-VL-8B-Instruct`

已通过项：

- 多模态非流式 `/v1/responses`
- 多模态流式 `/v1/responses`

### 本次修复

首次测试时暴露出一个模型分流问题：

- bridge 能识别多模态输入
- 但会把客户端请求中的文本模型名带到多模态上游
- 导致多模态上游返回 `404`

已修复为：

- 当请求切到多模态 upstream 时
- 如果客户端传的是文本 canonical 模型，或传的是映射到文本模型的 alias
- bridge 自动改写为多模态 upstream 的默认模型

对应回归测试见：

- [test_model_resolution.py](/Users/wangkq/work/mlx-code/codex-responses-bridge/tests/test_model_resolution.py:1)

## 3. 智谱公网 coder plan

### 上游信息

- URL: `https://open.bigmodel.cn/api/coding/paas/v4`
- 正确模型列表路径: `/models`
- `chat/completions` 路径: `/chat/completions`

### 实测可见模型

- `glm-4.5`
- `glm-4.5-air`
- `glm-4.6`
- `glm-4.7`
- `glm-5`
- `glm-5-turbo`
- `glm-5.1`

### 上游直连结论

- `/models` 可用。
- `/v1/models` 不可用，会返回 404。
- `glm-5.1`、`glm-5-turbo`、`glm-4.5`、`glm-4.5-air` 均可调用。
- `glm-5.1` 会返回 `reasoning_content` 和最终 `content`。

### bridge 验证结论

已通过项：

- `GET /health`
- `GET /v1/models`
- `GPT-5.5 -> glm-5.1` 别名映射
- `/v1/responses` 非流式转换
- `/v1/responses` 流式转换
- reasoning 和 output_text 还原

### 注意事项

当 `max_output_tokens` 过小时，上游可能在 reasoning 阶段就 `finish_reason=length`，导致最终正文为空。把 `max_output_tokens` 提升到 `256` 后，bridge 已验证可正确返回：

- reasoning item
- message item
- `output_text = "OK"`

### 推荐 GPT 到 GLM 适配

- `GPT-5.5 -> glm-5.1`
- `GPT-5.4 -> glm-5.1`
- `GPT-4.1 -> glm-4.5`
- `GPT-4.1-mini -> glm-4.5-air`
- `o4-mini -> glm-5-turbo`

## 4. DeepSeek 公网

### 上游信息

- URL: `https://api.deepseek.com/v1`
- 模型列表路径:
  - `https://api.deepseek.com/models`
  - `https://api.deepseek.com/v1/models`

### 实测可见模型

- `deepseek-v4-flash`
- `deepseek-v4-pro`

### 上游直连结论

- `deepseek-chat` 可调用，返回模型名实际为 `deepseek-v4-flash`。
- `deepseek-reasoner` 可调用，也返回模型名 `deepseek-v4-flash`，同时带 `reasoning_content`。
- tool call 支持正常。
- 流式 reasoning 增量支持正常。

### bridge 验证结论

已通过项：

- `GET /health`
- `GET /v1/models`
- `GPT-5.4 -> deepseek-chat`
- `GPT-5.5 -> deepseek-reasoner`
- `/v1/responses` 非流式普通文本
- `/v1/responses` 非流式 tool call
- `/v1/responses` 非流式 reasoning
- `/v1/responses` 流式 reasoning

### 推荐 GPT 到 DeepSeek 适配

- `GPT-5.5 -> deepseek-reasoner`
- `GPT-5.4 -> deepseek-chat`
- `GPT-4.1 -> deepseek-chat`
- `GPT-4.1-mini -> deepseek-chat`
- `o4-mini -> deepseek-chat`

### 说明

DeepSeek 当前对外显示的真实模型名与请求名存在别名关系：

- 请求 `deepseek-chat`，返回 `deepseek-v4-flash`
- 请求 `deepseek-reasoner`，返回 `deepseek-v4-flash`

这说明 DeepSeek 后端存在 provider 内部模型映射。bridge 当前按请求模型名发起调用，返回时尊重上游真实 `model` 字段。

## 5. 小米 MiMo 公网

### 上游信息

- URL: `https://api.xiaomimimo.com/v1`
- 路径:
  - `/models`
  - `/chat/completions`

### 实测可见模型

- `mimo-v2-flash`
- `mimo-v2-omni`
- `mimo-v2-pro`
- `mimo-v2-tts`
- `mimo-v2.5`
- `mimo-v2.5-pro`
- `mimo-v2.5-tts`
- `mimo-v2.5-tts-voiceclone`
- `mimo-v2.5-tts-voicedesign`

### 上游直连结论

- `mimo-v2.5-pro` 可调用。
- `mimo`、`mimo-latest`、`mimo-vl-1` 在该接口下不被支持。
- 非流式普通文本成功。
- function tool call 成功。
- 流式 reasoning 增量成功。
- 流式开始前会上送一行 `: PROCESSING`，bridge 当前可忽略该行并继续解析。

### bridge 验证结论

已通过项：

- `GET /health`
- `GET /v1/models`
- `GPT-5.4 -> mimo-v2.5-pro`
- `/v1/responses` 非流式普通文本
- `/v1/responses` 非流式 tool call
- `/v1/responses` 流式 reasoning

### 现象说明

MiMo 在“高 reasoning + 非流式”场景下存在一定波动：

- 同样的 `max_output_tokens=256`
- 有时会在 reasoning 阶段耗尽 token，导致 `finish_reason=length` 且正文 `content=""`
- 有时又能正常返回最终 `output_text="OK"`

bridge 抓包确认这种现象来自上游行为，而不是 bridge 丢失正文。

### 推荐 GPT 到 MiMo 适配

- `GPT-5.5 -> mimo-v2.5-pro`
- `GPT-5.4 -> mimo-v2.5-pro`
- `GPT-4.1 -> mimo-v2.5-pro`
- `GPT-4.1-mini -> mimo-v2-flash`
- `o4-mini -> mimo-v2-flash`

## 6. 阿里云百炼千问兼容模式

### 上游信息

- URL: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- 验证日期：`2026-05-30`
- 关键路径:
  - `/models`
  - `/chat/completions`

### 实测可见重点模型

- `qwen3.7-max`
- `qwen3.6-plus`
- `qwen3.6-flash`
- `qwen3-coder-plus`
- `qwen3-coder-flash`
- `qwen3-vl-plus`
- `qwen3-vl-flash`

### 上游直连结论

- `GET /models` 正常。
- `qwen3.7-max` 非流式请求成功，返回 `reasoning_content` 和最终 `content`。
- `qwen3.7-max` 适合当前 bridge 的 `Responses -> chat/completions` 文本转换验证。

### bridge 验证结论

本次使用单服务环境变量模式，本地端口：`127.0.0.1:8112`。

已通过项：

- `GET /health`
- `GET /v1/models`
- `GPT-5.5 -> qwen3.7-max` 别名映射
- `GPT-5.4 -> qwen3.6-plus` 别名映射
- `gpt-5.5 -> qwen3.7-max` 小写别名映射
- 未知模型名回落到默认上游 `qwen3.7-max`
- `/v1/responses` 非流式普通文本
- `/v1/responses` 流式 reasoning
- `/v1/responses` 流式 output_text
- `/v1/responses` 非流式 function_call
- `/v1/responses` 非流式 function_call_output 跟进
- `/v1/models` 正常暴露 canonical 模型和 alias 模型

### 抓包确认

bridge 抓包文件中已确认：

- `GPT-5.5` 被翻译为上游 `model=qwen3.7-max`
- `GPT-5.4` 被翻译为上游 `model=qwen3.6-plus`
- `gpt-5.5` 同样被翻译为上游 `model=qwen3.7-max`
- 未知模型名在默认策略 `default_upstream` 下被翻译为 `model=qwen3.7-max`
- `tool_choice=required` 已被改写为 `tool_choice=auto`

### 上游限制说明

本次还验证到一个真实上游限制，并已在 bridge 中补上兼容处理：

- 当使用 `qwen3.7-max` thinking 模式时
- 如果请求里带 `tool_choice=required`
- 百炼会直接返回 `400 InternalError.Algo.InvalidParameter`

错误核心信息：

- `The tool_choice parameter does not support being set to required or object in thinking mode`

后续兼容策略：

- bridge 现已对 `qwen37-token` provider 增加自动降级
- 当收到 `tool_choice=required` 或 function object 形式的 `tool_choice`
- 会在转发前改写为 `tool_choice=auto`
- 改写动作会记录在日志和抓包 `removed_fields` 中

### 兼容修复后复测结果

- 修复后再次发送 `tool_choice=required` 的 tool call 请求
- bridge 成功把请求转发到千问
- 上游返回 `finish_reason=tool_calls`
- bridge 正常还原为 `Responses` 的 `function_call` item

随后继续发送：

- `function_call`
- `function_call_output`
- 用户跟进消息

二轮请求也已成功，最终返回：

- `output_text = "TIME_OK"`

### 推荐 GPT 到千问适配

- `GPT-5.5 -> qwen3.7-max`
- `GPT-5.4 -> qwen3.6-plus`
- `GPT-5.4-mini -> qwen3.6-flash`
- `GPT-4.1 -> qwen3.6-plus`
- `GPT-4.1-mini -> qwen3.6-flash`
- `o4-mini -> qwen3.6-flash`
