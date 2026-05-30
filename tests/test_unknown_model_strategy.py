from codex_responses_bridge.model_aliases import resolve_client_model
from codex_responses_bridge.models import ServiceConfig, UpstreamConfig


def build_service(strategy: str) -> ServiceConfig:
    return ServiceConfig(
        name="svc",
        host="127.0.0.1",
        port=8090,
        protocol_mode="openai-chat",
        text_upstream=UpstreamConfig(
            provider="glm-code",
            base_url="http://example.com/v1",
            model="glm-5.1",
            api_key_env="API_KEY",
        ),
        model_aliases={"GPT-5.5": "glm-5.1"},
        unknown_model_strategy=strategy,
    )


def test_unknown_model_defaults_to_upstream_model():
    service = build_service("default_upstream")
    resolved, source = resolve_client_model(service, service.text_upstream, "some-unknown-model")
    assert resolved == "glm-5.1"
    assert source == "some-unknown-model"


def test_unknown_model_passthrough_strategy():
    service = build_service("passthrough")
    resolved, source = resolve_client_model(service, service.text_upstream, "some-unknown-model")
    assert resolved == "some-unknown-model"
    assert source is None
