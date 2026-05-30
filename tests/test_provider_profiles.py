from codex_responses_bridge.models import ServiceConfig, UpstreamConfig
from codex_responses_bridge.provider_profiles import build_public_model_entries, sanitize_openai_chat_payload


def build_service() -> ServiceConfig:
    return ServiceConfig(
        name="svc",
        host="127.0.0.1",
        port=8090,
        protocol_mode="openai-chat",
        text_upstream=UpstreamConfig(
            provider="glm-code",
            base_url="https://open.bigmodel.cn/api/paas/v4",
            model="GLM-5.1",
            api_key_env="ZHIPU_API_KEY",
        ),
        multimodal_upstream=UpstreamConfig(
            provider="local-vlm",
            base_url="http://127.0.0.1:33338/v1",
            model="Qwen/Qwen2.5-VL-7B-Instruct",
            api_key_env="LOCAL_VLM_API_KEY",
        ),
        model_aliases={"GPT-5.4": "GLM-5.1", "GPT-5.5": "GLM-5.1"},
    )


def test_build_public_model_entries_exposes_alias_and_canonical_models():
    entries = build_public_model_entries(build_service())
    ids = [item["id"] for item in entries]
    assert "GLM-5.1" in ids
    assert "Qwen/Qwen2.5-VL-7B-Instruct" in ids
    assert "GPT-5.4" in ids
    alias_entry = next(item for item in entries if item["id"] == "GPT-5.4")
    assert alias_entry["metadata"]["canonical_model"] == "GLM-5.1"


def test_sanitize_openai_chat_payload_for_multimodal_local_vlm():
    upstream = build_service().multimodal_upstream
    payload = {
        "model": "Qwen/Qwen2.5-VL-7B-Instruct",
        "messages": [{"role": "user", "content": []}],
        "tools": [{"type": "function", "function": {"name": "run"}}],
        "tool_choice": "auto",
        "parallel_tool_calls": True,
        "presence_penalty": 0.1,
        "frequency_penalty": 0.2,
        "stream_options": {"include_usage": True},
    }
    sanitized, removed = sanitize_openai_chat_payload(
        upstream=upstream,
        payload=payload,
        is_multimodal=True,
    )
    assert "tools" not in sanitized
    assert "tool_choice" not in sanitized
    assert "parallel_tool_calls" not in sanitized
    assert "presence_penalty" not in sanitized
    assert "frequency_penalty" not in sanitized
    assert "stream_options" in sanitized
    assert "tools" in removed


def test_sanitize_openai_chat_payload_strips_message_reasoning_for_non_deepseek():
    service = build_service()
    payload = {
        "model": "glm-5.1",
        "messages": [{"role": "assistant", "content": "", "reasoning_content": "想一想"}],
    }
    sanitized, removed = sanitize_openai_chat_payload(
        upstream=service.text_upstream,
        payload=payload,
        is_multimodal=False,
    )
    assert "reasoning_content" not in sanitized["messages"][0]
    assert "messages.reasoning_content" in removed


def test_sanitize_openai_chat_payload_keeps_message_reasoning_for_deepseek():
    service = ServiceConfig(
        name="svc",
        host="127.0.0.1",
        port=8090,
        protocol_mode="openai-chat",
        text_upstream=UpstreamConfig(
            provider="deepseek",
            base_url="https://api.deepseek.com/v1",
            model="deepseek-v4-pro",
            api_key_env="DEEPSEEK_API_KEY",
        ),
    )
    payload = {
        "model": "deepseek-v4-pro",
        "messages": [{"role": "assistant", "content": "", "reasoning_content": "想一想"}],
    }
    sanitized, removed = sanitize_openai_chat_payload(
        upstream=service.text_upstream,
        payload=payload,
        is_multimodal=False,
    )
    assert sanitized["messages"][0]["reasoning_content"] == "想一想"
    assert "messages.reasoning_content" not in removed
