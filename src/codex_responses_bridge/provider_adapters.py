from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import UpstreamConfig


@dataclass(frozen=True)
class PayloadAdaptationResult:
    payload: dict[str, Any]
    changed_fields: list[str]


def _adapt_qwen37_token_payload(payload: dict[str, Any]) -> PayloadAdaptationResult:
    adapted = dict(payload)
    changed_fields: list[str] = []

    tool_choice = adapted.get("tool_choice")
    if tool_choice == "required" or isinstance(tool_choice, dict):
        adapted["tool_choice"] = "auto"
        changed_fields.append("tool_choice:downgraded_to_auto")

    return PayloadAdaptationResult(payload=adapted, changed_fields=changed_fields)


def adapt_openai_chat_payload(
    *,
    upstream: UpstreamConfig,
    payload: dict[str, Any],
) -> PayloadAdaptationResult:
    if upstream.provider == "qwen37-token":
        return _adapt_qwen37_token_payload(payload)
    return PayloadAdaptationResult(payload=dict(payload), changed_fields=[])
