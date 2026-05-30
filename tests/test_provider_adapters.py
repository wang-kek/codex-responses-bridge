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
    assert result.payload["max_tokens"] == 4096
    assert result.changed_fields == ["tool_choice:downgraded_to_auto", "max_tokens:default_applied"]


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
    assert result.payload["max_tokens"] == 4096
    assert result.changed_fields == ["tool_choice:downgraded_to_auto", "max_tokens:default_applied"]


def test_adapt_qwen_keeps_tools_for_short_debug_failures():
    upstream = UpstreamConfig(
        provider="qwen37-token",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen3.7-max",
        api_key_env="DASHSCOPE_API_KEY",
    )
    payload = {
        "model": "qwen3.7-max",
        "messages": [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "run", "arguments": "{}"}}]},
            {"role": "tool", "tool_call_id": "call_1", "content": "Exit code: 1\ncommand failed"},
            {"role": "assistant", "tool_calls": [{"id": "call_2", "type": "function", "function": {"name": "run", "arguments": "{}"}}]},
            {"role": "tool", "tool_call_id": "call_2", "content": "not found"},
            {"role": "assistant", "tool_calls": [{"id": "call_3", "type": "function", "function": {"name": "run", "arguments": "{}"}}]},
            {"role": "tool", "tool_call_id": "call_3", "content": "still trying"},
        ],
        "tools": [{"type": "function", "function": {"name": "run", "parameters": {"type": "object", "properties": {}}}}],
        "parallel_tool_calls": True,
        "tool_choice": "auto",
    }
    result = adapt_openai_chat_payload(upstream=upstream, payload=payload)
    assert "tools" in result.payload
    assert "parallel_tool_calls" in result.payload
    assert result.payload["tool_choice"] == "auto"
    assert result.payload["max_tokens"] == 4096
    assert result.changed_fields == ["max_tokens:default_applied"]


def test_adapt_qwen_compacts_long_tool_history_without_disabling_tools():
    upstream = UpstreamConfig(
        provider="qwen37-token",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen3.7-max",
        api_key_env="DASHSCOPE_API_KEY",
    )
    messages = [{"role": "user", "content": "hi"}]
    for index in range(10):
        call_id = f"call_{index}"
        messages.append(
            {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": call_id,
                        "type": "function",
                        "function": {"name": "run", "arguments": "{}"},
                    }
                ],
            }
        )
        messages.append(
            {
                "role": "tool",
                "tool_call_id": call_id,
                "content": "Exit code: 1\ncommand failed",
            }
        )
    payload = {
        "model": "qwen3.7-max",
        "messages": messages,
        "tools": [{"type": "function", "function": {"name": "run", "parameters": {"type": "object", "properties": {}}}}],
        "parallel_tool_calls": True,
        "tool_choice": "auto",
    }
    result = adapt_openai_chat_payload(upstream=upstream, payload=payload)
    assert "tools" in result.payload
    assert "parallel_tool_calls" in result.payload
    assert result.payload["tool_choice"] == "auto"
    assert all("tool_calls" not in message for message in result.payload["messages"])
    assert all(message.get("role") != "tool" for message in result.payload["messages"])
    assert "tools:disabled_after_tool_loop" not in result.changed_fields
    assert "tool_choice:removed_after_tool_loop" not in result.changed_fields
    assert any(field.startswith("messages:tool_history_compacted_after_tool_loop:") for field in result.changed_fields)
    assert "max_tokens:default_applied" in result.changed_fields


def test_adapt_default_provider_applies_default_max_tokens():
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
    assert result.payload["max_tokens"] == 4096
    assert result.changed_fields == ["max_tokens:default_applied"]


def test_adapt_provider_omits_inline_images_from_tool_outputs():
    upstream = UpstreamConfig(
        provider="glm-code",
        base_url="https://open.bigmodel.cn/api/coding/paas/v4",
        model="glm-5.1",
        api_key_env="ZHIPU_API_KEY",
    )
    payload = {
        "model": "glm-5.1",
        "messages": [
            {"role": "user", "content": "看一下截图"},
            {
                "role": "tool",
                "tool_call_id": "call_1",
                "content": '[{"type":"input_image","image_url":"data:image/png;base64,AAAAAA=="}]',
            },
        ],
    }
    result = adapt_openai_chat_payload(upstream=upstream, payload=payload)
    assert "data:image/png;base64" not in result.payload["messages"][1]["content"]
    assert "inline image omitted by bridge" in result.payload["messages"][1]["content"]
    assert "messages:tool_inline_images_omitted:1" in result.changed_fields


def test_adapt_provider_repairs_invalid_tool_call_arguments():
    upstream = UpstreamConfig(
        provider="glm-code",
        base_url="https://open.bigmodel.cn/api/coding/paas/v4",
        model="glm-5.1",
        api_key_env="ZHIPU_API_KEY",
    )
    payload = {
        "model": "glm-5.1",
        "messages": [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "shell_command",
                            "arguments": '{"command": "unterminated',
                        },
                    }
                ],
            }
        ],
    }
    result = adapt_openai_chat_payload(upstream=upstream, payload=payload)
    repaired = result.payload["messages"][0]["tool_calls"][0]["function"]["arguments"]
    assert "_bridge_repaired_invalid_arguments" in repaired
    assert "messages:invalid_tool_arguments_repaired:1" in result.changed_fields


def test_adapt_zhipu_public_glm_applies_codex_history_guards():
    upstream = UpstreamConfig(
        provider="glm-code",
        base_url="https://open.bigmodel.cn/api/coding/paas/v4",
        model="glm-5.1",
        api_key_env="ZHIPU_API_KEY",
    )
    payload = {
        "model": "glm-5.1",
        "messages": [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_bad",
                        "type": "function",
                        "function": {
                            "name": "shell_command",
                            "arguments": '{"command": "Set-Content',
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "tool_call_id": "call_img",
                "content": '[{"type":"input_image","image_url":"data:image/png;base64,BBBBBB=="}]',
            },
        ],
        "stream": True,
    }
    result = adapt_openai_chat_payload(upstream=upstream, payload=payload)
    repaired = result.payload["messages"][0]["tool_calls"][0]["function"]["arguments"]
    compacted_tool_output = result.payload["messages"][1]["content"]
    assert result.payload["max_tokens"] == 4096
    assert "_bridge_repaired_invalid_arguments" in repaired
    assert "data:image/png;base64" not in compacted_tool_output
    assert "messages:invalid_tool_arguments_repaired:1" in result.changed_fields
    assert "messages:tool_inline_images_omitted:1" in result.changed_fields
    assert "max_tokens:default_applied" in result.changed_fields
