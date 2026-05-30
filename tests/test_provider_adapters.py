from codex_responses_bridge.models import UpstreamConfig
from codex_responses_bridge.provider_adapters import adapt_openai_chat_payload


def test_adapt_qwen_required_tool_choice_to_auto():
    upstream = UpstreamConfig(
        provider="qwen37-token",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen3.7-max",
        api_key_env="DASHSCOPE_API_KEY",
    )
    result = adapt_openai_chat_payload(
        upstream=upstream,
        payload={
            "model": "qwen3.7-max",
            "messages": [{"role": "user", "content": "hi"}],
            "tool_choice": "required",
        },
    )
    assert result.payload["tool_choice"] == "auto"
    assert result.changed_fields == ["tool_choice:downgraded_to_auto"]


def test_adapt_qwen_function_tool_choice_object_to_auto():
    upstream = UpstreamConfig(
        provider="qwen37-token",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen3.7-max",
        api_key_env="DASHSCOPE_API_KEY",
    )
    result = adapt_openai_chat_payload(
        upstream=upstream,
        payload={
            "model": "qwen3.7-max",
            "messages": [{"role": "user", "content": "hi"}],
            "tool_choice": {"type": "function", "function": {"name": "run"}},
        },
    )
    assert result.payload["tool_choice"] == "auto"
    assert result.changed_fields == ["tool_choice:downgraded_to_auto"]


def test_adapt_default_provider_keeps_payload_unchanged():
    upstream = UpstreamConfig(
        provider="glm-code",
        base_url="https://open.bigmodel.cn/api/coding/paas/v4",
        model="glm-5.1",
        api_key_env="ZHIPU_API_KEY",
    )
    payload = {
        "model": "glm-5.1",
        "messages": [{"role": "user", "content": "hi"}],
        "tool_choice": "required",
    }
    result = adapt_openai_chat_payload(upstream=upstream, payload=payload)
    assert result.payload == payload
    assert result.changed_fields == []
