from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from .models import UpstreamConfig


@dataclass(frozen=True)
class PayloadAdaptationResult:
    payload: dict[str, Any]
    changed_fields: list[str]


FAILURE_MARKERS = (
    "exit code: 1",
    "exit code: 2",
    "command not found",
    "not found",
    "file not found",
    "traceback",
    "error",
    "exception",
)


TOOL_LOOP_TURN_THRESHOLD = 20
TOOL_LOOP_RECENT_FAILURE_THRESHOLD = 4
DEFAULT_MAX_TOKENS = 4096
PROVIDER_DEFAULT_MAX_TOKENS = {
    "local-vlm": 2048,
}
INVALID_TOOL_ARGUMENTS_PREVIEW_CHARS = 4000
INLINE_IMAGE_PATTERN = re.compile(
    r"data:image/(?P<format>[a-zA-Z0-9.+-]+);base64,(?P<data>[A-Za-z0-9+/=\r\n]+)"
)


def _count_tool_turns(messages: Any) -> int:
    if not isinstance(messages, list):
        return 0
    count = 0
    for message in messages:
        if not isinstance(message, dict):
            continue
        if message.get("role") in {"tool", "assistant"} and (
            message.get("tool_call_id") or message.get("tool_calls")
        ):
            count += 1
    return count


def _is_failure_text(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in FAILURE_MARKERS)


def _count_recent_tool_failures(messages: Any, limit: int = 8) -> int:
    if not isinstance(messages, list):
        return 0
    failures = 0
    examined = 0
    for message in reversed(messages):
        if not isinstance(message, dict):
            continue
        if message.get("role") != "tool":
            continue
        content = message.get("content")
        text = content if isinstance(content, str) else str(content or "")
        if _is_failure_text(text):
            failures += 1
        examined += 1
        if examined >= limit:
            break
    return failures


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    return str(content or "")


def _apply_default_max_tokens(payload: dict[str, Any], upstream: UpstreamConfig) -> tuple[dict[str, Any], list[str]]:
    if "max_tokens" in payload or "max_completion_tokens" in payload:
        return payload, []

    adapted = dict(payload)
    adapted["max_tokens"] = PROVIDER_DEFAULT_MAX_TOKENS.get(upstream.provider, DEFAULT_MAX_TOKENS)
    return adapted, ["max_tokens:default_applied"]


def _omit_inline_images(text: str) -> tuple[str, int]:
    omitted_count = 0

    def replace(match: "re.Match[str]") -> str:
        nonlocal omitted_count
        omitted_count += 1
        image_format = match.group("format")
        image_chars = len(match.group("data"))
        return "[inline image omitted by bridge: image/{0}, base64_chars={1}]".format(
            image_format,
            image_chars,
        )

    return INLINE_IMAGE_PATTERN.sub(replace, text), omitted_count


def _compact_inline_images_in_tool_outputs(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    messages = payload.get("messages")
    if not isinstance(messages, list):
        return payload, []

    compacted_messages: list[dict[str, Any]] = []
    omitted_images = 0
    changed = False
    for message in messages:
        if not isinstance(message, dict):
            compacted_messages.append(message)
            continue
        if message.get("role") != "tool":
            compacted_messages.append(message)
            continue

        content = message.get("content")
        if not isinstance(content, str) or "data:image/" not in content:
            compacted_messages.append(message)
            continue

        compacted_content, count = _omit_inline_images(content)
        if count == 0:
            compacted_messages.append(message)
            continue

        compacted_message = dict(message)
        compacted_message["content"] = compacted_content
        compacted_messages.append(compacted_message)
        omitted_images += count
        changed = True

    if not changed:
        return payload, []

    adapted = dict(payload)
    adapted["messages"] = compacted_messages
    return adapted, ["messages:tool_inline_images_omitted:{0}".format(omitted_images)]


def _repair_invalid_tool_call_arguments(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    messages = payload.get("messages")
    if not isinstance(messages, list):
        return payload, []

    repaired_count = 0
    repaired_messages: list[dict[str, Any]] = []
    for message in messages:
        if not isinstance(message, dict):
            repaired_messages.append(message)
            continue
        tool_calls = message.get("tool_calls")
        if not isinstance(tool_calls, list):
            repaired_messages.append(message)
            continue

        repaired_tool_calls = []
        message_changed = False
        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                repaired_tool_calls.append(tool_call)
                continue
            function = tool_call.get("function")
            if not isinstance(function, dict):
                repaired_tool_calls.append(tool_call)
                continue

            arguments = function.get("arguments")
            if arguments is None:
                repaired_tool_calls.append(tool_call)
                continue
            if not isinstance(arguments, str):
                arguments = json.dumps(arguments, ensure_ascii=False)

            try:
                json.loads(arguments or "{}")
                repaired_tool_calls.append(tool_call)
                continue
            except Exception as exc:
                repaired_function = dict(function)
                repaired_function["arguments"] = json.dumps(
                    {
                        "_bridge_repaired_invalid_arguments": True,
                        "error": str(exc),
                        "raw_preview": arguments[:INVALID_TOOL_ARGUMENTS_PREVIEW_CHARS],
                    },
                    ensure_ascii=False,
                )
                repaired_tool_call = dict(tool_call)
                repaired_tool_call["function"] = repaired_function
                repaired_tool_calls.append(repaired_tool_call)
                repaired_count += 1
                message_changed = True

        if message_changed:
            repaired_message = dict(message)
            repaired_message["tool_calls"] = repaired_tool_calls
            repaired_messages.append(repaired_message)
        else:
            repaired_messages.append(message)

    if repaired_count == 0:
        return payload, []

    adapted = dict(payload)
    adapted["messages"] = repaired_messages
    return adapted, ["messages:invalid_tool_arguments_repaired:{0}".format(repaired_count)]


def _compact_tool_history_for_final_answer(messages: Any) -> tuple[Any, int]:
    if not isinstance(messages, list):
        return messages, 0

    compacted: list[dict[str, Any]] = []
    removed_count = 0

    for message in messages:
        if not isinstance(message, dict):
            continue
        if message.get("role") == "tool":
            removed_count += 1
            continue
        if message.get("role") == "assistant" and message.get("tool_calls"):
            removed_count += 1
            continue
        compacted.append(dict(message))

    if removed_count == 0:
        return messages, 0
    return compacted, removed_count


def _adapt_qwen37_token_payload(payload: dict[str, Any]) -> PayloadAdaptationResult:
    adapted = dict(payload)
    changed_fields: list[str] = []

    tool_choice = adapted.get("tool_choice")
    if tool_choice == "required" or isinstance(tool_choice, dict):
        adapted["tool_choice"] = "auto"
        changed_fields.append("tool_choice:downgraded_to_auto")

    messages = adapted.get("messages")
    tool_turns = _count_tool_turns(messages)
    recent_tool_failures = _count_recent_tool_failures(messages)
    if tool_turns >= TOOL_LOOP_TURN_THRESHOLD or recent_tool_failures >= TOOL_LOOP_RECENT_FAILURE_THRESHOLD:
        compacted_messages, removed_messages = _compact_tool_history_for_final_answer(messages)
        if removed_messages:
            adapted["messages"] = compacted_messages
            changed_fields.append(f"messages:tool_history_compacted_after_tool_loop:{removed_messages}")

    return PayloadAdaptationResult(payload=adapted, changed_fields=changed_fields)


def adapt_openai_chat_payload(
    *,
    upstream: UpstreamConfig,
    payload: dict[str, Any],
) -> PayloadAdaptationResult:
    changed_fields: list[str] = []
    if upstream.provider == "qwen37-token":
        result = _adapt_qwen37_token_payload(payload)
        adapted = result.payload
        changed_fields.extend(result.changed_fields)
    else:
        adapted = dict(payload)

    adapted, image_changes = _compact_inline_images_in_tool_outputs(adapted)
    changed_fields.extend(image_changes)

    adapted, tool_argument_changes = _repair_invalid_tool_call_arguments(adapted)
    changed_fields.extend(tool_argument_changes)

    adapted, max_token_changes = _apply_default_max_tokens(adapted, upstream)
    changed_fields.extend(max_token_changes)

    return PayloadAdaptationResult(payload=adapted, changed_fields=changed_fields)
