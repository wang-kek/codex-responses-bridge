from __future__ import annotations

from .models import ProviderProfile, ServiceConfig, UpstreamConfig


DEFAULT_PROVIDER_PROFILE = ProviderProfile(name="default-openai-chat")

PROVIDER_PROFILES: dict[str, ProviderProfile] = {
    "deepseek": ProviderProfile(
        name="deepseek",
        supports_tools=True,
        supports_tool_choice=True,
        supports_stream_options=True,
        supports_response_format=False,
        supports_reasoning=False,
        supports_penalties=True,
    ),
    "glm-code": ProviderProfile(
        name="glm-code",
        supports_tools=True,
        supports_tool_choice=True,
        supports_stream_options=True,
        supports_response_format=False,
        supports_reasoning=True,
        supports_penalties=True,
    ),
    "qwen37-token": ProviderProfile(
        name="qwen37-token",
        supports_tools=True,
        supports_tool_choice=True,
        supports_stream_options=True,
        supports_response_format=False,
        supports_reasoning=False,
        supports_penalties=True,
    ),
    "mimo": ProviderProfile(
        name="mimo",
        supports_tools=True,
        supports_tool_choice=True,
        supports_stream_options=True,
        supports_response_format=False,
        supports_reasoning=False,
        supports_penalties=True,
    ),
    "local-vlm": ProviderProfile(
        name="local-vlm",
        supports_tools=False,
        supports_tool_choice=False,
        supports_stream_options=True,
        supports_response_format=False,
        supports_reasoning=False,
        supports_penalties=False,
        supports_multimodal_tools=False,
    ),
    "glm-vlm": ProviderProfile(
        name="glm-vlm",
        supports_tools=False,
        supports_tool_choice=False,
        supports_stream_options=True,
        supports_response_format=False,
        supports_reasoning=False,
        supports_penalties=False,
        supports_multimodal_tools=False,
    ),
}


def get_provider_profile(provider: str) -> ProviderProfile:
    return PROVIDER_PROFILES.get(provider, DEFAULT_PROVIDER_PROFILE)


def build_public_model_entries(service: ServiceConfig) -> list[dict]:
    entries: list[dict] = []
    seen_ids: set[str] = set()

    def add_entry(model_id: str, owned_by: str, kind: str, canonical_model: str, provider: str) -> None:
        if not model_id or model_id in seen_ids:
            return
        seen_ids.add(model_id)
        entries.append(
            {
                "id": model_id,
                "object": "model",
                "owned_by": owned_by,
                "metadata": {
                    "service": service.name,
                    "kind": kind,
                    "provider": provider,
                    "canonical_model": canonical_model,
                },
            }
        )

    add_entry(service.text_upstream.model, service.text_upstream.provider, "canonical", service.text_upstream.model, service.text_upstream.provider)
    if service.multimodal_upstream is not None:
        add_entry(
            service.multimodal_upstream.model,
            service.multimodal_upstream.provider,
            "canonical-multimodal",
            service.multimodal_upstream.model,
            service.multimodal_upstream.provider,
        )

    for alias, target in sorted(service.model_aliases.items()):
        add_entry(alias, "alias", "alias", target, service.text_upstream.provider)
    return entries


def sanitize_openai_chat_payload(
    *,
    upstream: UpstreamConfig,
    payload: dict,
    is_multimodal: bool,
) -> tuple[dict, list[str]]:
    profile = get_provider_profile(upstream.provider)
    sanitized = dict(payload)
    removed_fields: list[str] = []

    if not profile.supports_tools:
        for key in ("tools", "parallel_tool_calls"):
            if key in sanitized:
                sanitized.pop(key, None)
                removed_fields.append(key)
    if not profile.supports_tool_choice and "tool_choice" in sanitized:
        sanitized.pop("tool_choice", None)
        removed_fields.append("tool_choice")
    if not profile.supports_stream_options and "stream_options" in sanitized:
        sanitized.pop("stream_options", None)
        removed_fields.append("stream_options")
    if not profile.supports_penalties:
        for key in ("presence_penalty", "frequency_penalty"):
            if key in sanitized:
                sanitized.pop(key, None)
                removed_fields.append(key)
    if not profile.supports_reasoning and "reasoning" in sanitized:
        sanitized.pop("reasoning", None)
        removed_fields.append("reasoning")
    if not profile.supports_response_format and "response_format" in sanitized:
        sanitized.pop("response_format", None)
        removed_fields.append("response_format")
    if is_multimodal and not profile.supports_multimodal_tools:
        for key in ("tools", "tool_choice", "parallel_tool_calls"):
            if key in sanitized:
                sanitized.pop(key, None)
                if key not in removed_fields:
                    removed_fields.append(key)
    if upstream.provider != "deepseek":
        messages = sanitized.get("messages")
        if isinstance(messages, list):
            cleaned_messages = []
            stripped_message_reasoning = False
            for message in messages:
                if not isinstance(message, dict):
                    cleaned_messages.append(message)
                    continue
                if "reasoning_content" in message:
                    message = dict(message)
                    message.pop("reasoning_content", None)
                    stripped_message_reasoning = True
                cleaned_messages.append(message)
            sanitized["messages"] = cleaned_messages
            if stripped_message_reasoning:
                removed_fields.append("messages.reasoning_content")

    if upstream.extra_body:
        sanitized.update(upstream.extra_body)
    return sanitized, removed_fields
