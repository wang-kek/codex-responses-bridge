import json

from codex_responses_bridge.translators.responses_openai import (
    convert_chat_to_responses_payload,
    convert_responses_to_openai_chat,
    has_multimodal_content,
    stream_openai_chat_to_responses,
)


def test_has_multimodal_content():
    body_input = [
        {
            "type": "message",
            "role": "user",
            "content": [
                {"type": "input_text", "text": "look at this"},
                {"type": "input_image", "image_url": {"url": "https://example.com/demo.png"}},
            ],
        }
    ]
    assert has_multimodal_content(body_input) is True


def test_convert_responses_to_openai_chat():
    payload = convert_responses_to_openai_chat(
        {
            "instructions": "system rule",
            "input": [
                {
                    "type": "message",
                    "role": "user",
                    "content": "hello",
                }
            ],
            "stream": True,
            "max_output_tokens": 512,
        },
        "deepseek-chat",
    )
    assert payload["model"] == "deepseek-chat"
    assert payload["stream"] is True
    assert payload["max_tokens"] == 512
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][1]["content"] == "hello"


def test_convert_responses_to_openai_chat_with_tool_history():
    payload = convert_responses_to_openai_chat(
        {
            "input": [
                {"type": "message", "role": "user", "content": "hi"},
                {"type": "function_call", "call_id": "call_1", "name": "lookup", "arguments": '{"q":"x"}'},
                {"type": "function_call_output", "call_id": "call_1", "output": {"result": "ok"}},
            ]
        },
        "GLM-5.1",
    )
    assert payload["messages"][1]["tool_calls"][0]["function"]["name"] == "lookup"
    assert payload["messages"][2]["role"] == "tool"
    assert "ok" in payload["messages"][2]["content"]


def test_convert_responses_to_openai_chat_preserves_reasoning_for_tool_history():
    payload = convert_responses_to_openai_chat(
        {
            "input": [
                {"type": "message", "role": "user", "content": "hi"},
                {
                    "type": "reasoning",
                    "content": [{"type": "reasoning_text", "text": "需要先查一下"}],
                },
                {"type": "function_call", "call_id": "call_1", "name": "lookup", "arguments": '{"q":"x"}'},
                {"type": "function_call_output", "call_id": "call_1", "output": "ok"},
            ]
        },
        "deepseek-v4-pro",
    )
    assert payload["messages"][1]["reasoning_content"] == "需要先查一下"
    assert payload["messages"][1]["tool_calls"][0]["function"]["name"] == "lookup"


def test_convert_chat_to_responses_payload():
    payload = convert_chat_to_responses_payload(
        {
            "id": "chatcmpl_1",
            "model": "GLM-5.1",
            "choices": [
                {
                    "message": {
                        "content": "你好",
                        "reasoning_content": "先分析一下",
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {"name": "get_weather", "arguments": '{"city":"beijing"}'},
                            }
                        ],
                    }
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        },
        "GLM-5.1",
    )
    output_types = [item["type"] for item in payload["output"]]
    assert output_types == ["reasoning", "message", "function_call"]
    assert payload["usage"]["total_tokens"] == 15


class FakeStreamResponse:
    def __init__(self, lines):
        self._lines = lines

    async def aiter_lines(self):
        for line in self._lines:
            yield line


async def _collect_stream(lines):
    items = []
    async for chunk in stream_openai_chat_to_responses(
        FakeStreamResponse(lines),
        response_id="resp_1",
        model="GLM-5.1",
        request_max_output_tokens=256,
    ):
        items.append(chunk.decode("utf-8"))
    return items


def test_stream_openai_chat_to_responses():
    lines = [
        'data: {"choices":[{"delta":{"reasoning_content":"想一想"}}]}',
        'data: {"choices":[{"delta":{"content":"你"}}]}',
        'data: {"choices":[{"delta":{"content":"好","tool_calls":[{"index":0,"id":"call_1","type":"function","function":{"name":"run","arguments":"{\\"cmd\\""}}]}}]}',
        'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":":\\"pwd\\"}"}}]}}],"usage":{"prompt_tokens":3,"completion_tokens":2,"total_tokens":5}}',
        "data: [DONE]",
    ]
    import asyncio

    chunks = asyncio.run(_collect_stream(lines))
    joined = "\n".join(chunks)
    assert "response.reasoning_text.delta" in joined
    assert "response.output_text.delta" in joined
    assert "response.function_call_arguments.done" in joined
    assert "response.completed" in joined
    assert '"text":"你好"' in joined
