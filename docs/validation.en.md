# Validation Notes

This document records real integration checks for `codex-responses-bridge`.

Updated: May 30, 2026

## Covered upstreams

- Local Zhipu text model
- Local multimodal model
- Zhipu public `coder plan`
- DeepSeek public API
- Xiaomi MiMo public API
- Alibaba DashScope Qwen compatible mode

## Summary

- Local Zhipu text proxy: passed
- Local multimodal proxy: passed
- Zhipu coder plan proxy: passed
- DeepSeek proxy: passed
- Xiaomi MiMo proxy: passed with one upstream-side caveat
- DashScope Qwen proxy: passed with one upstream-side tool-choice caveat

## Important findings

- Local text deployments should override default aliases so `GPT-5.4` / `GPT-5.5` map to the real local model such as `glm-5.1-fp8`.
- Multimodal routing required a fix so multimodal requests fall back to the multimodal upstream model instead of the text model.
- Zhipu coder plan uses `/models`, not `/v1/models`, on the upstream side.
- DeepSeek currently resolves both `deepseek-chat` and `deepseek-reasoner` to `deepseek-v4-flash` in real responses.
- MiMo may sometimes consume the full token budget in reasoning during non-stream requests, leaving the final assistant text empty even when the bridge behaves correctly.
- On May 30, 2026, DashScope Qwen compatible mode accepted `qwen3.7-max` text bridging and alias mapping. The upstream rejected `tool_choice=required` in thinking mode, so the bridge now downgrades that case to `tool_choice=auto` for the `qwen37-token` provider.
- After that compatibility fix, a real tool-call round trip also passed: the first request produced a `function_call`, and a follow-up `function_call_output` request completed with final text output.

See the Chinese report for the detailed validation breakdown:

- [validation.zh-CN.md](/Users/wangkq/work/mlx-code/codex-responses-bridge/docs/validation.zh-CN.md)
