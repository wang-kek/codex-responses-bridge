import os
from pathlib import Path

from codex_responses_bridge.config import load_services_from_yaml
from codex_responses_bridge.config import load_single_service_from_env


def test_load_services_from_yaml():
    config_path = Path(__file__).resolve().parents[1] / "configs" / "services.example.yaml"
    services = load_services_from_yaml(config_path)
    assert len(services) == 5
    assert services[0].name == "glm-local-main"
    assert services[0].text_upstream.provider == "glm-code"
    assert services[0].multimodal_upstream is not None
    assert services[0].host == "0.0.0.0"
    assert services[0].model_aliases["GPT-5.5"] == "glm-5.1-fp8"
    assert services[1].model_aliases["GPT-5.5"] == "glm-5.1"
    assert services[1].text_upstream.base_url == "https://open.bigmodel.cn/api/coding/paas/v4"
    assert services[2].model_aliases["GPT-5.5"] == "deepseek-v4-pro"
    assert services[2].model_aliases["GPT-5.4"] == "deepseek-v4-pro"
    assert services[3].model_aliases["GPT-5.5"] == "qwen3.7-max"
    assert services[3].model_aliases["GPT-5.4"] == "qwen3.7-max"
    assert services[3].unknown_model_strategy == "default_upstream"


def test_load_single_service_from_env_alias_override():
    old = dict(os.environ)
    try:
        os.environ["CRB_UPSTREAM_PROVIDER"] = "glm-code"
        os.environ["CRB_UPSTREAM_BASE_URL"] = "http://127.0.0.1:8000/v1"
        os.environ["CRB_UPSTREAM_MODEL"] = "glm-5.1-fp8"
        os.environ["CRB_MODEL_ALIASES"] = "GPT-5.4=glm-5.1-fp8,GPT-5.5=glm-5.1-fp8"
        service = load_single_service_from_env()
        assert service.host == "0.0.0.0"
        assert service.model_aliases["GPT-4.1"] == "glm-4.7"
        assert service.model_aliases["GPT-5.4"] == "glm-5.1-fp8"
        assert service.model_aliases["GPT-5.5"] == "glm-5.1-fp8"
        assert service.unknown_model_strategy == "default_upstream"
    finally:
        os.environ.clear()
        os.environ.update(old)


def test_load_single_service_from_env_uses_provider_defaults():
    old = dict(os.environ)
    try:
        os.environ["CRB_UPSTREAM_PROVIDER"] = "glm-code"
        service = load_single_service_from_env()
        assert service.text_upstream.base_url == "https://open.bigmodel.cn/api/coding/paas/v4"
        assert service.text_upstream.model == "glm-5.1"
        assert service.model_aliases["GPT-5.5"] == "glm-5.1"
    finally:
        os.environ.clear()
        os.environ.update(old)


def test_load_services_from_yaml_supports_direct_api_key():
    tmp = Path(__file__).resolve().parent / "_tmp_services.yaml"
    tmp.write_text(
        """
language: zh-CN
services:
  - name: direct-key
    port: 9000
    provider: deepseek
    base_url: https://api.deepseek.com/v1
    api_key: direct-key-value
    model: deepseek-v4-pro
""".strip(),
        encoding="utf-8",
    )
    try:
        services = load_services_from_yaml(tmp)
        assert services[0].text_upstream.api_key == "direct-key-value"
        assert services[0].text_upstream.api_key_env == "OPENAI_API_KEY"
    finally:
        if tmp.exists():
            tmp.unlink()
