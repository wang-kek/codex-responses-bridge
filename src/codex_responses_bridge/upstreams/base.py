from __future__ import annotations

from dataclasses import dataclass

from ..models import ServiceConfig, UpstreamConfig


@dataclass(frozen=True)
class SelectedUpstream:
    config: UpstreamConfig
    purpose: str


def select_upstream(service: ServiceConfig, *, has_multimodal_input: bool) -> SelectedUpstream:
    if has_multimodal_input and service.multimodal_upstream is not None:
        return SelectedUpstream(config=service.multimodal_upstream, purpose="multimodal")
    return SelectedUpstream(config=service.text_upstream, purpose="text")

