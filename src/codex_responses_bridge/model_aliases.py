from __future__ import annotations

from typing import Dict, Optional, Tuple

from .models import ServiceConfig, UpstreamConfig


def _lookup_alias(aliases: Dict[str, str], requested_model: str) -> Optional[str]:
    direct = aliases.get(requested_model)
    if direct:
        return direct

    lowered_requested = requested_model.lower()
    for alias, target in aliases.items():
        if alias.lower() == lowered_requested:
            return target
    return None


def resolve_client_model(
    service: ServiceConfig,
    upstream: UpstreamConfig,
    requested_model: Optional[str],
) -> Tuple[str, Optional[str]]:
    normalized_requested = (requested_model or "").strip()
    if not normalized_requested:
        return upstream.model, None

    if normalized_requested == upstream.model:
        return upstream.model, None

    mapped_model = _lookup_alias(service.model_aliases, normalized_requested)
    if mapped_model:
        return mapped_model, normalized_requested

    if service.unknown_model_strategy == "default_upstream":
        return upstream.model, normalized_requested

    return normalized_requested, None


def resolve_model_for_selected_upstream(
    *,
    service: ServiceConfig,
    upstream: UpstreamConfig,
    requested_model: Optional[str],
    is_multimodal: bool,
) -> Tuple[str, Optional[str]]:
    resolved_model, alias_from = resolve_client_model(service, upstream, requested_model)
    if not is_multimodal:
        return resolved_model, alias_from

    normalized_requested = (requested_model or "").strip()
    if not normalized_requested:
        return upstream.model, alias_from

    if resolved_model == upstream.model:
        return resolved_model, alias_from

    if normalized_requested == service.text_upstream.model:
        return upstream.model, normalized_requested

    mapped_from_alias = _lookup_alias(service.model_aliases, normalized_requested)
    if mapped_from_alias == service.text_upstream.model:
        return upstream.model, normalized_requested

    return resolved_model, alias_from
