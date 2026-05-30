from codex_responses_bridge.model_aliases import resolve_client_model
from codex_responses_bridge.models import ServiceConfig, UpstreamConfig


def build_service():
    return ServiceConfig(
        name="glm-service",
        host="127.0.0.1",
        port=8091,
        protocol_mode="openai-chat",
        text_upstream=UpstreamConfig(
            provider="glm-code",
            base_url="https://open.bigmodel.cn/api/paas/v4",
            model="GLM-5.1",
            api_key_env="ZHIPU_API_KEY",
        ),
        model_aliases={
            "GPT-5.4": "GLM-5.1",
            "GPT-5.5": "GLM-5.1",
        },
    )


def test_resolve_client_model_alias_hit():
    service = build_service()
    resolved, alias_from = resolve_client_model(service, service.text_upstream, "GPT-5.5")
    assert resolved == "GLM-5.1"
    assert alias_from == "GPT-5.5"


def test_resolve_client_model_alias_miss_uses_requested_name():
    service = build_service()
    resolved, alias_from = resolve_client_model(service, service.text_upstream, "custom-model")
    assert resolved == "GLM-5.1"
    assert alias_from == "custom-model"


def test_resolve_client_model_empty_uses_default_upstream_model():
    service = build_service()
    resolved, alias_from = resolve_client_model(service, service.text_upstream, "")
    assert resolved == "GLM-5.1"
    assert alias_from is None


def test_resolve_client_model_alias_is_case_insensitive():
    service = build_service()
    resolved, alias_from = resolve_client_model(service, service.text_upstream, "gpt-5.4")
    assert resolved == "GLM-5.1"
    assert alias_from == "gpt-5.4"
