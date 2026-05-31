from codex_responses_bridge.models import UpstreamConfig
from codex_responses_bridge.upstreams.openai import is_loopback_upstream


def test_is_loopback_upstream():
    assert is_loopback_upstream(
        UpstreamConfig(
            provider="deepseek",
            base_url="http://127.0.0.1:8000/v1",
            model="deepseek-v4-pro",
            api_key_env="",
        )
    )
    assert not is_loopback_upstream(
        UpstreamConfig(
            provider="deepseek",
            base_url="https://api.deepseek.com/v1",
            model="deepseek-v4-pro",
            api_key_env="DEEPSEEK_API_KEY",
        )
    )
