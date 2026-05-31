from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse

import httpx

from ..models import UpstreamConfig


def build_chat_completions_url(config: UpstreamConfig) -> str:
    return f"{config.base_url.rstrip('/')}/chat/completions"


def is_loopback_upstream(config: UpstreamConfig) -> bool:
    host = (urlparse(config.base_url).hostname or "").lower()
    return host in {"127.0.0.1", "localhost", "::1"}


def build_headers(config: UpstreamConfig) -> dict[str, str]:
    api_key = config.api_key.strip() if config.api_key else os.environ.get(config.api_key_env, "").strip()
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


async def post_chat_completions(
    client: httpx.AsyncClient,
    *,
    config: UpstreamConfig,
    payload: dict[str, Any],
) -> httpx.Response:
    return await client.post(
        build_chat_completions_url(config),
        json=payload,
        headers=build_headers(config),
        timeout=config.timeout_seconds,
    )


def stream_chat_completions(
    client: httpx.AsyncClient,
    *,
    config: UpstreamConfig,
    payload: dict[str, Any],
):
    return client.stream(
        "POST",
        build_chat_completions_url(config),
        json=payload,
        headers=build_headers(config),
        timeout=config.timeout_seconds,
    )
