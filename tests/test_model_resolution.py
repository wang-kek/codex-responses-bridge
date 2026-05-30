from codex_responses_bridge.model_aliases import resolve_model_for_selected_upstream
from codex_responses_bridge.models import ServiceConfig, UpstreamConfig


def build_service() -> ServiceConfig:
    return ServiceConfig(
        name="svc",
        host="127.0.0.1",
        port=1,
        protocol_mode="openai-chat",
        text_upstream=UpstreamConfig(
            provider="glm-code",
            base_url="http://text/v1",
            model="glm-5.1-fp8",
            api_key_env="TEXT_KEY",
        ),
        multimodal_upstream=UpstreamConfig(
            provider="local-vlm",
            base_url="http://mm/v1",
            model="Qwen/Qwen3-VL-8B-Instruct",
            api_key_env="MM_KEY",
        ),
        model_aliases={
            "GPT-5.4": "glm-5.1-fp8",
            "GPT-5.5": "glm-5.1-fp8",
        },
    )


def test_multimodal_request_with_text_model_falls_back_to_mm_model():
    service = build_service()
    resolved, alias_from = resolve_model_for_selected_upstream(
        service=service,
        upstream=service.multimodal_upstream,
        requested_model="glm-5.1-fp8",
        is_multimodal=True,
    )
    assert resolved == "Qwen/Qwen3-VL-8B-Instruct"
    assert alias_from == "glm-5.1-fp8"


def test_multimodal_request_with_text_alias_falls_back_to_mm_model():
    service = build_service()
    resolved, alias_from = resolve_model_for_selected_upstream(
        service=service,
        upstream=service.multimodal_upstream,
        requested_model="GPT-5.4",
        is_multimodal=True,
    )
    assert resolved == "Qwen/Qwen3-VL-8B-Instruct"
    assert alias_from == "GPT-5.4"
