import os
from pathlib import Path

from codex_responses_bridge.config import load_services_from_yaml
from codex_responses_bridge.config import load_single_service_from_env


def test_load_services_from_yaml():
    config_path = Path(__file__).resolve().parents[1] / "configs" / "services.example.yaml"
    services = load_services_from_yaml(config_path)
    assert len(services) == 6
    assert services[0].name == "glm-local-main"
    assert services[0].text_upstream.provider == "glm-code"
    assert services[0].multimodal_upstream is not None
    assert services[0].host == "0.0.0.0"
    assert services[0].model_aliases["GPT-5.5"] == "glm-5.1-fp8"
    assert services[1].name == "deepseek-local"
    assert services[1].text_upstream.base_url == "http://127.0.0.1:8000/v1"
    assert services[1].text_upstream.api_key_env == "DEEPSEEK_LOCAL_API_KEY"
    assert services[1].text_upstream.model == "deepseek-v4-flash"
    assert services[1].multimodal_upstream is not None
    assert services[1].multimodal_upstream.provider == "local-vlm"
    assert services[1].multimodal_upstream.base_url == "http://192.168.1.251:33338/v1"
    assert services[1].multimodal_upstream.model == "Qwen/Qwen3-VL-8B-Instruct"
    assert services[1].model_aliases["GPT-5.5"] == "deepseek-v4-flash"
    assert services[1].model_aliases["GPT-5.4"] == "deepseek-v4-flash"
    assert services[2].model_aliases["GPT-5.5"] == "glm-5.1"
    assert services[2].text_upstream.base_url == "https://open.bigmodel.cn/api/coding/paas/v4"
    assert services[3].model_aliases["GPT-5.5"] == "deepseek-v4-pro"
    assert services[3].model_aliases["GPT-5.4"] == "deepseek-v4-pro"
    assert services[3].multimodal_upstream is not None
    assert services[3].multimodal_upstream.provider == "local-vlm"
    assert services[3].multimodal_upstream.base_url == "http://192.168.1.251:33338/v1"
    assert services[3].multimodal_upstream.model == "Qwen/Qwen3-VL-8B-Instruct"
    assert services[4].model_aliases["GPT-5.5"] == "qwen3.7-max"
    assert services[4].model_aliases["GPT-5.4"] == "qwen3.7-max"
    assert services[4].unknown_model_strategy == "default_upstream"


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


def test_load_services_from_yaml_supports_keyless_upstream():
    tmp = Path(__file__).resolve().parent / "_tmp_keyless_services.yaml"
    tmp.write_text(
        """
language: zh-CN
services:
  - name: keyless-local
    port: 9001
    provider: deepseek
    base_url: http://127.0.0.1:8000/v1
    api_key_env: ""
    model: deepseek-v4-pro
""".strip(),
        encoding="utf-8",
    )
    try:
        services = load_services_from_yaml(tmp)
        assert services[0].text_upstream.api_key == ""
        assert services[0].text_upstream.api_key_env == ""
    finally:
        if tmp.exists():
            tmp.unlink()


def test_load_services_from_yaml_skips_disabled_services():
    tmp = Path(__file__).resolve().parent / "_tmp_disabled_services.yaml"
    tmp.write_text(
        """
language: zh-CN
services:
  - name: disabled-local
    enabled: false
    port: 9100
    provider: deepseek
    base_url: http://127.0.0.1:8000/v1
    model: deepseek-v4-flash
  - name: enabled-public
    enabled: true
    port: 9101
    provider: deepseek
    base_url: https://api.deepseek.com/v1
    model: deepseek-v4-pro
""".strip(),
        encoding="utf-8",
    )
    try:
        services = load_services_from_yaml(tmp)
        assert len(services) == 1
        assert services[0].name == "enabled-public"
        assert services[0].port == 9101
    finally:
        if tmp.exists():
            tmp.unlink()
