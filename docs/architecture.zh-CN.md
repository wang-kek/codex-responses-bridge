# 架构设计

## 设计目标

- 精准解决 Codex `Responses API` 到多种上游协议的转换问题
- 优先围绕 OpenAI-style Chat Completions 建设
- 对 Anthropic 模式保留清晰的扩展接口
- 允许一个本地端口绑定一组文本/多模态上游
- 保留测试日志、请求抓取、调试可观测性

## 运行模式

### 单服务模式

- 通过环境变量启动一个本地端口
- 适合本机调试、单模型验证、快速接入

### 多服务模式

- 通过 YAML 配置一次性启动多个本地监听端口
- 每个端口可绑定不同的文本上游和多模态上游
- 支持 `defaults` 合并公共参数
- 支持 `upstreams` 复用上游定义

## 核心模块

### `config.py`

- 解析环境变量模式
- 解析 YAML 配置文件模式
- 生成统一服务配置对象
- 维护客户端模型别名到上游模型名的映射配置
- 支持通过 `CRB_MODEL_ALIASES` 或 `CRB_MODEL_ALIASES_JSON` 覆盖环境变量模式默认映射
- 内置映射按 provider 区分，避免所有服务共享一个默认目标模型
- 支持未知模型策略，默认回落到服务默认上游模型

### `provider_profiles.py`

- 定义不同 provider 的字段能力画像
- 在发送上游前裁剪不兼容字段
- 暂时聚焦 `tools`、`tool_choice`、`stream_options`、`penalty` 等通用差异

### `provider_adapters.py`

- 负责 provider 特定的请求改写规则
- 用于承接“不是通用能力开关，而是厂商真实行为差异”的兼容逻辑
- 当前已包含千问兼容模式的 `tool_choice=required -> auto` 降级

### `app.py`

- 创建 FastAPI 应用
- 暴露 `/health`、`/v1/models`、`/v1/responses`

### `translators/responses_openai.py`

- 负责 `Responses -> Chat Completions` 请求映射
- 负责 `Chat Completions -> Responses` 结果映射
- 负责 `Chat Completions SSE -> Responses SSE` 流式事件映射
- 在请求进入上游前完成客户端模型名标准化

## 模型暴露策略

- `/v1/models` 同时暴露真实 canonical 模型和客户端别名模型
- alias 条目在 `metadata.canonical_model` 中指向真实上游模型
- 这样 Codex 客户端和内部实际模型配置可以解耦
- alias 匹配对客户端名称大小写不敏感

## 未知模型策略

- 默认策略：`default_upstream`
- 当客户端提交一个未命中 alias、也不是当前上游 canonical 模型的名字时
- bridge 默认不会原样透传，而是回落到当前服务绑定的默认上游模型
- 这样可以避免客户端随手传一个陌生模型名时出现不可预期的路由失败

### `upstreams/openai.py`

- 面向 OpenAI-style 上游的 HTTP 访问封装
- 负责头部认证、URL 拼接、流式转发

### `request_capture.py`

- 记录原始请求、转换后请求、上游响应摘要
- 用于调试、回归测试和协议对比

## 国际化

- 默认文档语言：中文
- 英文文档：同步维护核心设计与启动说明
- 模型映射依据单独整理在 `docs/model-mapping.zh-CN.md`
