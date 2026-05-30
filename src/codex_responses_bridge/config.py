from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from .models import ServiceConfig, UpstreamConfig


DEFAULT_PRESET_BASE_URLS = {
    "deepseek": "https://api.deepseek.com/v1",
    "glm-code": "https://open.bigmodel.cn/api/coding/paas/v4",
    "qwen37-token": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "mimo": "https://api.xiaomimimo.com/v1",
}

DEFAULT_PRESET_MODELS = {
    "deepseek": "deepseek-v4-pro",
    "glm-code": "glm-5.1",
    "qwen37-token": "qwen3.7-max",
    "mimo": "mimo-v2.5-pro",
}

DEFAULT_MODEL_ALIASES: Dict[str, str] = {}

PROVIDER_DEFAULT_MODEL_ALIASES = {
    "deepseek": {
        "GPT-5.5": "deepseek-v4-pro",
        "GPT-5.4": "deepseek-v4-flash",
        "GPT-5.4-mini": "deepseek-v4-flash",
        "GPT-4.1": "deepseek-v4-flash",
        "GPT-4.1-mini": "deepseek-v4-flash",
        "o4-mini": "deepseek-v4-flash",
    },
    "glm-code": {
        "GPT-5.5": "glm-5.1",
        "GPT-5.4": "glm-5-turbo",
        "GPT-5.4-mini": "glm-4.6",
        "GPT-4.1": "glm-4.7",
        "GPT-4.1-mini": "glm-4.6",
        "o4-mini": "glm-5-turbo",
    },
    "qwen37-token": {
        "GPT-5.5": "qwen3.7-max",
        "GPT-5.4": "qwen3.6-plus",
        "GPT-5.4-mini": "qwen3.6-flash",
        "GPT-4.1": "qwen3.6-plus",
        "GPT-4.1-mini": "qwen3.6-flash",
        "o4-mini": "qwen3.6-flash",
    },
    "mimo": {
        "GPT-5.5": "mimo-v2.5-pro",
        "GPT-5.4": "mimo-v2.5-pro",
        "GPT-5.4-mini": "mimo-v2-flash",
        "GPT-4.1": "mimo-v2-pro",
        "GPT-4.1-mini": "mimo-v2-flash",
        "o4-mini": "mimo-v2-flash",
    },
}


def _as_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _build_upstream_config(raw: Dict[str, Any], fallback_provider: str = "custom") -> UpstreamConfig:
    provider = (raw.get("provider") or fallback_provider).strip()
    base_url = (raw.get("base_url") or DEFAULT_PRESET_BASE_URLS.get(provider) or "").rstrip("/")
    model = (raw.get("model") or "").strip()
    api_key_env = (raw.get("api_key_env") or "OPENAI_API_KEY").strip()
    protocol_mode = (raw.get("protocol_mode") or "openai-chat").strip()
    timeout_seconds = int(raw.get("timeout_seconds") or 180)
    if not base_url:
        raise ValueError(f"missing base_url for upstream provider={provider}")
    if not model:
        raise ValueError(f"missing model for upstream provider={provider}")
    return UpstreamConfig(
        provider=provider,
        base_url=base_url,
        model=model,
        api_key_env=api_key_env,
        protocol_mode=protocol_mode,
        timeout_seconds=timeout_seconds,
        extra_body=raw.get("extra_body") if isinstance(raw.get("extra_body"), dict) else {},
    )


def _merge_dict(base: Any, override: Any) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    if isinstance(base, dict):
        result.update(base)
    if isinstance(override, dict):
        result.update(override)
    return result


def _resolve_upstream_from_entry(
    *,
    item: Dict[str, Any],
    key: str,
    upstream_templates: Dict[str, Any],
) -> Optional[UpstreamConfig]:
    raw_value = item.get(key)
    ref_name = item.get(f"{key}_ref")
    if raw_value is None and not ref_name:
        return None

    template: Dict[str, Any] = {}
    if ref_name:
        template = upstream_templates.get(ref_name) or {}
        if not isinstance(template, dict):
            raise ValueError(f"upstream ref {ref_name!r} for {key} is not a mapping")

    resolved_raw = _merge_dict(template, raw_value)
    fallback_provider = str(resolved_raw.get("provider") or template.get("provider") or "custom")
    return _build_upstream_config(resolved_raw, fallback_provider=fallback_provider)


def _parse_aliases(raw: Any) -> Dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    aliases: Dict[str, str] = {}
    for key, value in raw.items():
        if key is None or value is None:
            continue
        source = str(key).strip()
        target = str(value).strip()
        if not source or not target:
            continue
        aliases[source] = target
    return aliases


def _parse_aliases_from_env() -> Dict[str, str]:
    raw_json = os.environ.get("CRB_MODEL_ALIASES_JSON", "").strip()
    if raw_json:
        try:
            payload = yaml.safe_load(raw_json)
        except Exception as exc:
            raise ValueError(f"invalid CRB_MODEL_ALIASES_JSON: {exc}") from exc
        return {**DEFAULT_MODEL_ALIASES, **_parse_aliases(payload)}

    raw_pairs = os.environ.get("CRB_MODEL_ALIASES", "").strip()
    if not raw_pairs:
        return DEFAULT_MODEL_ALIASES.copy()

    parsed: Dict[str, str] = {}
    for pair in raw_pairs.split(","):
        item = pair.strip()
        if not item:
            continue
        if "=" not in item:
            raise ValueError(
                "invalid CRB_MODEL_ALIASES entry; expected comma-separated source=target pairs"
            )
        source, target = item.split("=", 1)
        source = source.strip()
        target = target.strip()
        if not source or not target:
            raise ValueError(
                "invalid CRB_MODEL_ALIASES entry; source and target must both be non-empty"
            )
        parsed[source] = target
    return {**DEFAULT_MODEL_ALIASES, **parsed}


def _provider_default_aliases(provider: str) -> Dict[str, str]:
    return dict(PROVIDER_DEFAULT_MODEL_ALIASES.get(provider, {}))


def load_single_service_from_env() -> ServiceConfig:
    provider = os.environ.get("CRB_UPSTREAM_PROVIDER", "deepseek").strip()
    base_url = os.environ.get("CRB_UPSTREAM_BASE_URL", DEFAULT_PRESET_BASE_URLS.get(provider, "")).strip()
    text_upstream = _build_upstream_config(
        {
            "provider": provider,
            "base_url": base_url,
            "model": os.environ.get("CRB_UPSTREAM_MODEL", DEFAULT_PRESET_MODELS.get(provider, "")),
            "api_key_env": os.environ.get("CRB_UPSTREAM_API_KEY_ENV", "CRB_UPSTREAM_API_KEY"),
            "protocol_mode": os.environ.get("CRB_UPSTREAM_PROTOCOL_MODE", "openai-chat"),
            "timeout_seconds": os.environ.get("CRB_UPSTREAM_TIMEOUT", "180"),
        },
        fallback_provider=provider,
    )

    multimodal_provider = os.environ.get("CRB_MM_UPSTREAM_PROVIDER", "").strip()
    multimodal_upstream = None
    if multimodal_provider:
        multimodal_upstream = _build_upstream_config(
            {
                "provider": multimodal_provider,
                "base_url": os.environ.get("CRB_MM_UPSTREAM_BASE_URL", DEFAULT_PRESET_BASE_URLS.get(multimodal_provider, "")),
                "model": os.environ.get("CRB_MM_UPSTREAM_MODEL", ""),
                "api_key_env": os.environ.get("CRB_MM_UPSTREAM_API_KEY_ENV", "CRB_MM_UPSTREAM_API_KEY"),
                "protocol_mode": os.environ.get("CRB_MM_UPSTREAM_PROTOCOL_MODE", "openai-chat"),
                "timeout_seconds": os.environ.get("CRB_MM_UPSTREAM_TIMEOUT", "180"),
            },
            fallback_provider=multimodal_provider,
        )

    return ServiceConfig(
        name=os.environ.get("CRB_SERVICE_NAME", "default-service").strip(),
        host=os.environ.get("CRB_HOST", "127.0.0.1").strip(),
        port=int(os.environ.get("CRB_PORT", "8090")),
        protocol_mode=os.environ.get("CRB_PROTOCOL_MODE", "openai-chat").strip(),
        text_upstream=text_upstream,
        multimodal_upstream=multimodal_upstream,
        model_aliases={**_provider_default_aliases(provider), **_parse_aliases_from_env()},
        unknown_model_strategy=os.environ.get("CRB_UNKNOWN_MODEL_STRATEGY", "default_upstream").strip() or "default_upstream",
        language=os.environ.get("CRB_LANGUAGE", "zh-CN").strip(),
        request_capture_enabled=_as_bool(os.environ.get("CRB_CAPTURE_ENABLED"), default=False),
        request_capture_directory=os.environ.get("CRB_CAPTURE_DIR", "./captures").strip(),
    )


def load_services_from_yaml(path: Union[str, os.PathLike]) -> List[ServiceConfig]:
    config_path = Path(path)
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    defaults = data.get("defaults") or {}
    language = data.get("language", defaults.get("language", "zh-CN"))
    capture = data.get("request_capture") or defaults.get("request_capture") or {}
    upstream_templates = data.get("upstreams") or {}
    default_host = defaults.get("host", "127.0.0.1")
    default_protocol_mode = defaults.get("protocol_mode", "openai-chat")
    default_unknown_model_strategy = defaults.get("unknown_model_strategy", "default_upstream")
    services = []
    for item in data.get("services") or []:
        text_upstream = _resolve_upstream_from_entry(
            item=item,
            key="text_upstream",
            upstream_templates=upstream_templates,
        )
        if text_upstream is None:
            raise ValueError(f"service {item.get('name', 'service')} missing text_upstream or text_upstream_ref")
        multimodal_upstream = _resolve_upstream_from_entry(
            item=item,
            key="multimodal_upstream",
            upstream_templates=upstream_templates,
        )
        services.append(
            ServiceConfig(
                name=item.get("name", "service"),
                host=item.get("host", default_host),
                port=int(item.get("port", 8090)),
                protocol_mode=item.get("protocol_mode", default_protocol_mode),
                text_upstream=text_upstream,
                multimodal_upstream=multimodal_upstream,
                model_aliases={**_provider_default_aliases(text_upstream.provider), **_parse_aliases(item.get("model_aliases"))},
                unknown_model_strategy=item.get("unknown_model_strategy", default_unknown_model_strategy),
                language=item.get("language", language),
                request_capture_enabled=bool(capture.get("enabled", False)),
                request_capture_directory=str(capture.get("directory", "./captures")),
                extra_metadata=item.get("extra_metadata") or {},
            )
        )
    if not services:
        raise ValueError(f"no services defined in config file: {config_path}")
    return services


def load_runtime_services() -> List[ServiceConfig]:
    if _as_bool(os.environ.get("CRB_USE_CONFIG_FILE"), default=False):
        config_file = os.environ.get("CRB_CONFIG_FILE", "./configs/services.example.yaml").strip()
        return load_services_from_yaml(config_file)
    return [load_single_service_from_env()]
