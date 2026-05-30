from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class UpstreamConfig:
    provider: str
    base_url: str
    model: str
    api_key_env: str
    protocol_mode: str = "openai-chat"
    timeout_seconds: int = 180
    extra_body: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ServiceConfig:
    name: str
    host: str
    port: int
    protocol_mode: str
    text_upstream: UpstreamConfig
    multimodal_upstream: Optional[UpstreamConfig] = None
    model_aliases: dict[str, str] = field(default_factory=dict)
    unknown_model_strategy: str = "default_upstream"
    language: str = "zh-CN"
    request_capture_enabled: bool = False
    request_capture_directory: str = "./captures"
    extra_metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderProfile:
    name: str
    supports_tools: bool = True
    supports_tool_choice: bool = True
    supports_stream_options: bool = True
    supports_response_format: bool = False
    supports_reasoning: bool = False
    supports_penalties: bool = True
    supports_multimodal_tools: bool = False
