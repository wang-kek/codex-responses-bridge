from __future__ import annotations

import json
import time
import uuid
from typing import Any, AsyncIterator, Dict, List, Optional


TEXT_PART_TYPES = {"text", "input_text", "output_text", "reasoning_text"}
IMAGE_PART_TYPES = {"input_image", "image_url"}


def _json_dumps(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def sse_event(event: str, payload: Dict[str, Any]) -> bytes:
    payload["type"] = event
    return f"event: {event}\ndata: {_json_dumps(payload)}\n\n".encode("utf-8")


def build_failed_response_event(
    *,
    response_id: str,
    model: str,
    message: str,
    error_type: str = "upstream_error",
) -> bytes:
    return sse_event(
        "response.failed",
        {
            "response": {
                "id": response_id,
                "object": "response",
                "status": "failed",
                "model": model,
                "error": {
                    "message": message,
                    "type": error_type,
                },
                "output": [],
                "usage": None,
            }
        },
    )


def has_multimodal_content(input_items: Any) -> bool:
    if not isinstance(input_items, list):
        return False
    for item in input_items:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "message":
            continue
        content = item.get("content")
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") in IMAGE_PART_TYPES:
                    return True
    return False


def extract_text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for part in content:
        if isinstance(part, str):
            parts.append(part)
            continue
        if isinstance(part, dict) and part.get("type") in TEXT_PART_TYPES:
            parts.append(part.get("text", ""))
    return "\n".join(item for item in parts if item)


def extract_reasoning_text(item: Dict[str, Any]) -> str:
    content_text = extract_text_from_content(item.get("content"))
    if content_text:
        return content_text
    return extract_text_from_content(item.get("summary"))


def normalize_image_url(value: Any) -> Optional[Dict[str, Any]]:
    if isinstance(value, str) and value:
        return {"url": value}
    if isinstance(value, dict) and value.get("url"):
        result = {"url": value["url"]}
        if value.get("detail"):
            result["detail"] = value["detail"]
        return result
    return None


def map_response_part_to_chat_part(part: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    part_type = part.get("type")
    if part_type in TEXT_PART_TYPES:
        return {"type": "text", "text": part.get("text", "")}
    if part_type in IMAGE_PART_TYPES:
        image_url = normalize_image_url(part.get("image_url") or part.get("url"))
        if image_url:
            return {"type": "image_url", "image_url": image_url}
    if part_type == "input_file":
        image_url = normalize_image_url(part.get("file_url") or part.get("image_url") or part.get("url"))
        if image_url:
            return {"type": "image_url", "image_url": image_url}
        if part.get("file_data"):
            return {
                "type": "text",
                "text": "[input_file provided but binary file parsing is not implemented by this bridge.]",
            }
    if "text" in part:
        return {"type": "text", "text": part.get("text", "")}
    return None


def convert_response_content_to_chat_content(content: Any) -> Any:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return str(content)

    chat_parts: List[Dict[str, Any]] = []
    text_buffer: List[str] = []
    for part in content:
        if isinstance(part, str):
            text_buffer.append(part)
            continue
        if not isinstance(part, dict):
            continue
        mapped = map_response_part_to_chat_part(part)
        if not mapped:
            continue
        if mapped.get("type") == "text":
            text_buffer.append(mapped.get("text", ""))
            continue
        if text_buffer:
            chat_parts.append({"type": "text", "text": "\n".join(item for item in text_buffer if item)})
            text_buffer = []
        chat_parts.append(mapped)

    if chat_parts:
        if text_buffer:
            chat_parts.append({"type": "text", "text": "\n".join(item for item in text_buffer if item)})
        return chat_parts
    return "\n".join(item for item in text_buffer if item)


def stringify_tool_output(output: Any) -> str:
    if output is None:
        return ""
    if isinstance(output, str):
        return output
    return json.dumps(output, ensure_ascii=False)


def map_tools_to_openai(tools: Any) -> Optional[List[Dict[str, Any]]]:
    if tools is None:
        return None
    if not isinstance(tools, list):
        return None
    mapped: List[Dict[str, Any]] = []
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        tool_type = tool.get("type")
        if tool_type != "function":
            continue
        if isinstance(tool.get("function"), dict):
            function = tool["function"]
            if function.get("name"):
                mapped.append({"type": "function", "function": function})
            continue
        if tool.get("name"):
            mapped.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters") or {"type": "object", "properties": {}},
                    },
                }
            )
    return mapped


def normalize_tool_choice(tool_choice: Any) -> Any:
    if tool_choice in (None, "auto", "none", "required"):
        return tool_choice
    if isinstance(tool_choice, dict) and tool_choice.get("type") == "function":
        if "function" in tool_choice:
            return tool_choice
        if tool_choice.get("name"):
            return {"type": "function", "function": {"name": tool_choice["name"]}}
    return tool_choice


def normalize_response_format(response_format: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(response_format, dict):
        return None
    fmt_type = response_format.get("type")
    if fmt_type == "json_object":
        return {"type": "json_object"}
    if fmt_type == "text":
        return {"type": "text"}
    if fmt_type == "json_schema":
        json_schema = response_format.get("json_schema")
        if isinstance(json_schema, dict) and isinstance(json_schema.get("schema"), dict):
            return {"type": "json_schema", "json_schema": json_schema}
    return None


def append_tool_call_to_messages(
    messages: List[Dict[str, Any]],
    tool_call: Dict[str, Any],
    reasoning_content: str,
) -> str:
    if messages and messages[-1].get("role") == "assistant":
        assistant_message = messages[-1]
        assistant_message.setdefault("content", "")
        assistant_message.setdefault("tool_calls", []).append(tool_call)
        if reasoning_content and not assistant_message.get("reasoning_content"):
            assistant_message["reasoning_content"] = reasoning_content
            return ""
        return reasoning_content

    message = {
        "role": "assistant",
        "content": "",
        "tool_calls": [tool_call],
    }
    if reasoning_content:
        message["reasoning_content"] = reasoning_content
        reasoning_content = ""
    messages.append(message)
    return reasoning_content


def convert_responses_to_openai_chat(body: Dict[str, Any], model: str) -> Dict[str, Any]:
    messages: List[Dict[str, Any]] = []
    known_tool_calls: Dict[str, Dict[str, Any]] = {}
    pending_reasoning_content = ""

    instructions = body.get("instructions")
    if instructions:
        messages.append({"role": "system", "content": extract_text_from_content(instructions)})

    input_data = body.get("input")
    if isinstance(input_data, str):
        messages.append({"role": "user", "content": input_data})
    elif isinstance(input_data, list):
        for item in input_data:
            if isinstance(item, str):
                messages.append({"role": "user", "content": item})
                continue
            if not isinstance(item, dict):
                continue

            item_type = item.get("type")
            if item_type in (None, "message"):
                role = item.get("role", "user")
                if role == "developer":
                    role = "system"
                if role not in {"system", "user", "assistant", "tool"}:
                    role = "user"
                message = {
                    "role": role,
                    "content": convert_response_content_to_chat_content(item.get("content", "")),
                }
                if role == "assistant" and pending_reasoning_content:
                    message["reasoning_content"] = pending_reasoning_content
                    pending_reasoning_content = ""
                messages.append(message)
            elif item_type == "reasoning":
                pending_reasoning_content = extract_reasoning_text(item)
            elif item_type == "function_call":
                call_id = item.get("call_id") or f"call_{uuid.uuid4().hex[:12]}"
                name = item.get("name") or ""
                arguments = item.get("arguments") or ""
                known_tool_calls[call_id] = {"name": name, "arguments": arguments}
                tool_call = {
                    "id": call_id,
                    "type": "function",
                    "function": {"name": name, "arguments": arguments},
                }
                pending_reasoning_content = append_tool_call_to_messages(
                    messages,
                    tool_call,
                    pending_reasoning_content,
                )
            elif item_type == "function_call_output":
                call_id = item.get("call_id", "")
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": stringify_tool_output(item.get("output", "")),
                    }
                )
    elif input_data is not None:
        messages.append({"role": "user", "content": str(input_data)})

    chat_body: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": bool(body.get("stream", False)),
    }
    if "temperature" in body:
        chat_body["temperature"] = body["temperature"]
    if "top_p" in body:
        chat_body["top_p"] = body["top_p"]
    if "presence_penalty" in body:
        chat_body["presence_penalty"] = body["presence_penalty"]
    if "frequency_penalty" in body:
        chat_body["frequency_penalty"] = body["frequency_penalty"]
    if "stop" in body:
        chat_body["stop"] = body["stop"]
    if "max_output_tokens" in body:
        chat_body["max_tokens"] = body["max_output_tokens"]
    elif "max_tokens" in body:
        chat_body["max_tokens"] = body["max_tokens"]
    if "parallel_tool_calls" in body:
        chat_body["parallel_tool_calls"] = bool(body["parallel_tool_calls"])
    if "response_format" in body:
        normalized = normalize_response_format(body.get("response_format"))
        if normalized is not None:
            chat_body["response_format"] = normalized
    if isinstance(body.get("text"), dict):
        normalized = normalize_response_format(body["text"].get("format"))
        if normalized is not None:
            chat_body["response_format"] = normalized
    if "reasoning" in body:
        chat_body["reasoning"] = body["reasoning"]

    mapped_tools = map_tools_to_openai(body.get("tools"))
    if mapped_tools is not None:
        chat_body["tools"] = mapped_tools
    if "tool_choice" in body:
        normalized_tool_choice = normalize_tool_choice(body.get("tool_choice"))
        if normalized_tool_choice is not None:
            chat_body["tool_choice"] = normalized_tool_choice
    if body.get("stream"):
        chat_body["stream_options"] = {"include_usage": True}
    return chat_body


def make_message_item(text: str, *, item_id: Optional[str] = None, status: str = "completed") -> Dict[str, Any]:
    return {
        "id": item_id or f"msg_{uuid.uuid4().hex[:12]}",
        "type": "message",
        "status": status,
        "role": "assistant",
        "content": [{"type": "output_text", "text": text, "annotations": [], "logprobs": []}],
    }


def make_reasoning_item(text: str, *, item_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    return {
        "id": item_id or f"rs_{uuid.uuid4().hex[:12]}",
        "type": "reasoning",
        "summary": [{"type": "summary_text", "text": text}],
        "content": [{"type": "reasoning_text", "text": text}],
    }


def make_function_call_item(tool_call: Dict[str, Any], *, item_id: Optional[str] = None) -> Dict[str, Any]:
    function = tool_call.get("function") or {}
    return {
        "id": item_id or f"fc_{uuid.uuid4().hex[:12]}",
        "type": "function_call",
        "status": "completed",
        "call_id": tool_call.get("id") or f"call_{uuid.uuid4().hex[:12]}",
        "name": function.get("name", ""),
        "arguments": function.get("arguments", ""),
    }


def convert_chat_to_responses_payload(chat_response: Dict[str, Any], default_model: str) -> Dict[str, Any]:
    choices = chat_response.get("choices") or []
    message = choices[0].get("message", {}) if choices else {}
    content = extract_text_from_content(message.get("content"))
    reasoning_text = message.get("reasoning_content") or message.get("reasoning") or ""
    output_items: List[Dict[str, Any]] = []

    reasoning_item = make_reasoning_item(reasoning_text)
    if reasoning_item:
        output_items.append(reasoning_item)
    if content:
        output_items.append(make_message_item(content))
    for tool_call in message.get("tool_calls") or []:
        output_items.append(make_function_call_item(tool_call))

    usage = chat_response.get("usage") or {}
    input_tokens = int(usage.get("prompt_tokens", 0) or 0)
    output_tokens = int(usage.get("completion_tokens", 0) or 0)
    total_tokens = int(usage.get("total_tokens", input_tokens + output_tokens) or (input_tokens + output_tokens))
    response_model = chat_response.get("model") or default_model

    return {
        "id": chat_response.get("id") or f"resp_{uuid.uuid4().hex[:12]}",
        "object": "response",
        "created_at": chat_response.get("created", int(time.time())),
        "status": "completed",
        "background": False,
        "error": None,
        "incomplete_details": None,
        "instructions": None,
        "max_output_tokens": None,
        "max_tool_calls": None,
        "model": response_model,
        "output": output_items,
        "parallel_tool_calls": bool(message.get("tool_calls")),
        "previous_response_id": None,
        "reasoning": {
            "effort": None,
            "summary": [{"type": "summary_text", "text": reasoning_text}] if reasoning_text else [],
        },
        "service_tier": "default",
        "store": False,
        "text": {"format": {"type": "text"}},
        "usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
        },
        "output_text": content,
    }


async def stream_openai_chat_to_responses(
    upstream_response: Any,
    *,
    response_id: str,
    model: str,
    request_max_output_tokens: Optional[int] = None,
) -> AsyncIterator[bytes]:
    created_at = int(time.time())
    content_index = 0
    full_text = ""
    reasoning_text = ""
    input_tokens = 0
    output_tokens = 0
    total_tokens = 0

    reasoning_item_id = f"rs_{uuid.uuid4().hex[:12]}"
    message_item_id = f"msg_{uuid.uuid4().hex[:12]}"
    message_started = False
    reasoning_started = False
    message_output_index: Optional[int] = None
    reasoning_output_index: Optional[int] = None
    next_output_index = 0

    tool_calls_by_index: Dict[int, Dict[str, Any]] = {}
    tool_item_id_by_index: Dict[int, str] = {}
    tool_output_index_by_index: Dict[int, int] = {}
    tool_order: List[int] = []

    def make_response(
        status: str,
        output: List[Dict[str, Any]],
        error: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {
            "id": response_id,
            "object": "response",
            "created_at": created_at,
            "status": status,
            "background": False,
            "error": error,
            "incomplete_details": None,
            "instructions": None,
            "max_output_tokens": request_max_output_tokens,
            "max_tool_calls": None,
            "model": model,
            "output": output,
            "parallel_tool_calls": bool(tool_calls_by_index),
            "previous_response_id": None,
            "reasoning": {
                "effort": None,
                "summary": [{"type": "summary_text", "text": reasoning_text}] if reasoning_text else [],
            },
            "service_tier": "default",
            "store": False,
            "text": {"format": {"type": "text"}},
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens or (input_tokens + output_tokens),
            },
            "output_text": full_text,
        }

    def ensure_message_started() -> List[bytes]:
        nonlocal message_started, message_output_index, next_output_index
        if message_started:
            return []
        message_started = True
        message_output_index = next_output_index
        next_output_index += 1
        return [
            sse_event(
                "response.output_item.added",
                {
                    "output_index": message_output_index,
                    "item": {
                        "id": message_item_id,
                        "type": "message",
                        "status": "in_progress",
                        "role": "assistant",
                        "content": [],
                    },
                },
            ),
            sse_event(
                "response.content_part.added",
                {
                    "item_id": message_item_id,
                    "output_index": message_output_index,
                    "content_index": content_index,
                    "part": {
                        "type": "output_text",
                        "text": "",
                        "annotations": [],
                        "logprobs": [],
                    },
                },
            ),
        ]

    def ensure_reasoning_started() -> List[bytes]:
        nonlocal reasoning_started, reasoning_output_index, next_output_index
        if reasoning_started:
            return []
        reasoning_started = True
        reasoning_output_index = next_output_index
        next_output_index += 1
        return [
            sse_event(
                "response.output_item.added",
                {
                    "output_index": reasoning_output_index,
                    "item": {
                        "id": reasoning_item_id,
                        "type": "reasoning",
                        "summary": [],
                        "content": [],
                    },
                },
            ),
            sse_event(
                "response.content_part.added",
                {
                    "item_id": reasoning_item_id,
                    "output_index": reasoning_output_index,
                    "content_index": 0,
                    "part": {
                        "type": "reasoning_text",
                        "text": "",
                    },
                },
            ),
        ]

    def merge_tool_delta(delta_tool_call: Dict[str, Any]) -> int:
        index = int(delta_tool_call.get("index", len(tool_calls_by_index)))
        current = tool_calls_by_index.setdefault(
            index,
            {
                "id": "",
                "type": "function",
                "function": {"name": "", "arguments": ""},
            },
        )
        if delta_tool_call.get("id"):
            current["id"] = delta_tool_call["id"]
        if delta_tool_call.get("type"):
            current["type"] = delta_tool_call["type"]
        function = delta_tool_call.get("function") or {}
        if function.get("name"):
            current["function"]["name"] = function["name"]
        if "arguments" in function:
            current["function"]["arguments"] += function.get("arguments") or ""
        return index

    def ensure_tool_started(index: int) -> List[bytes]:
        nonlocal next_output_index
        if index in tool_output_index_by_index:
            return []
        tool_order.append(index)
        tool_output_index_by_index[index] = next_output_index
        next_output_index += 1
        tool_item_id_by_index[index] = f"fc_{uuid.uuid4().hex[:12]}"
        tool_call = tool_calls_by_index[index]
        return [
            sse_event(
                "response.output_item.added",
                {
                    "output_index": tool_output_index_by_index[index],
                    "item": {
                        "id": tool_item_id_by_index[index],
                        "type": "function_call",
                        "status": "in_progress",
                        "call_id": tool_call.get("id") or f"call_{index}",
                        "name": (tool_call.get("function") or {}).get("name", ""),
                        "arguments": "",
                    },
                },
            )
        ]

    yield sse_event("response.created", {"response": make_response("in_progress", [])})
    yield sse_event("response.in_progress", {"response": make_response("in_progress", [])})

    async for line in upstream_response.aiter_lines():
        line = line.strip()
        if not line or not line.startswith("data:"):
            continue
        raw = line[5:].strip()
        if raw == "[DONE]":
            break
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue

        usage = data.get("usage") or {}
        input_tokens = int(usage.get("prompt_tokens", input_tokens) or input_tokens)
        output_tokens = int(usage.get("completion_tokens", output_tokens) or output_tokens)
        total_tokens = int(usage.get("total_tokens", total_tokens) or total_tokens)

        choices = data.get("choices") or []
        if not choices:
            continue
        delta = (choices[0].get("delta") or {})
        reasoning_delta = delta.get("reasoning") or delta.get("reasoning_content") or ""
        if reasoning_delta:
            reasoning_text += reasoning_delta
            for event in ensure_reasoning_started():
                yield event
            yield sse_event(
                "response.reasoning_text.delta",
                {
                    "item_id": reasoning_item_id,
                    "output_index": reasoning_output_index,
                    "content_index": 0,
                    "delta": reasoning_delta,
                },
            )

        text_delta = delta.get("content") or ""
        if text_delta:
            full_text += text_delta
            for event in ensure_message_started():
                yield event
            yield sse_event(
                "response.output_text.delta",
                {
                    "item_id": message_item_id,
                    "output_index": message_output_index,
                    "content_index": content_index,
                    "delta": text_delta,
                    "obfuscation": "",
                },
            )

        for delta_tool_call in delta.get("tool_calls") or []:
            index = merge_tool_delta(delta_tool_call)
            for event in ensure_tool_started(index):
                yield event
            function_delta = (delta_tool_call.get("function") or {}).get("arguments")
            if function_delta is not None:
                yield sse_event(
                    "response.function_call_arguments.delta",
                    {
                        "item_id": tool_item_id_by_index[index],
                        "output_index": tool_output_index_by_index[index],
                        "call_id": tool_calls_by_index[index].get("id") or f"call_{index}",
                        "delta": function_delta,
                    },
                )

    if total_tokens == 0:
        total_tokens = input_tokens + output_tokens

    completed_output: List[Dict[str, Any]] = []
    completed_by_index: Dict[int, Dict[str, Any]] = {}

    if reasoning_text and reasoning_output_index is not None:
        reasoning_item = make_reasoning_item(reasoning_text, item_id=reasoning_item_id)
        if reasoning_item:
            completed_by_index[reasoning_output_index] = reasoning_item
            yield sse_event(
                "response.reasoning_text.done",
                {
                    "item_id": reasoning_item_id,
                    "output_index": reasoning_output_index,
                    "content_index": 0,
                    "text": reasoning_text,
                },
            )
            yield sse_event(
                "response.content_part.done",
                {
                    "item_id": reasoning_item_id,
                    "output_index": reasoning_output_index,
                    "content_index": 0,
                    "part": {"type": "reasoning_text", "text": reasoning_text},
                },
            )
            yield sse_event(
                "response.output_item.done",
                {
                    "output_index": reasoning_output_index,
                    "item": reasoning_item,
                },
            )

    if (full_text or message_started) and message_output_index is not None:
        message_item = make_message_item(full_text, item_id=message_item_id, status="completed")
        completed_by_index[message_output_index] = message_item
        yield sse_event(
            "response.output_text.done",
            {
                "item_id": message_item_id,
                "output_index": message_output_index,
                "content_index": content_index,
                "text": full_text,
                "logprobs": [],
            },
        )
        yield sse_event(
            "response.content_part.done",
            {
                "item_id": message_item_id,
                "output_index": message_output_index,
                "content_index": content_index,
                "part": {
                    "type": "output_text",
                    "text": full_text,
                    "annotations": [],
                    "logprobs": [],
                },
            },
        )
        yield sse_event(
            "response.output_item.done",
            {
                "output_index": message_output_index,
                "item": message_item,
            },
        )

    for index in tool_order:
        tool_item = make_function_call_item(tool_calls_by_index[index], item_id=tool_item_id_by_index[index])
        completed_by_index[tool_output_index_by_index[index]] = tool_item
        yield sse_event(
            "response.function_call_arguments.done",
            {
                "item_id": tool_item["id"],
                "output_index": tool_output_index_by_index[index],
                "call_id": tool_item["call_id"],
                "arguments": tool_item["arguments"],
            },
        )
        yield sse_event(
            "response.output_item.done",
            {
                "output_index": tool_output_index_by_index[index],
                "item": tool_item,
            },
        )

    for index in sorted(completed_by_index):
        completed_output.append(completed_by_index[index])

    yield sse_event(
        "response.completed",
        {
            "response": make_response("completed", completed_output),
        },
    )
