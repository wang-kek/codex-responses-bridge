from __future__ import annotations

import logging
import os


def configure_logging() -> None:
    level_name = os.environ.get("CRB_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def summarize_payload(payload: object, limit: int = 1000) -> str:
    text = repr(payload)
    if len(text) <= limit:
        return text
    return text[:limit] + "...(truncated)"

