from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def capture_protocol_event(
    *,
    enabled: bool,
    directory: str,
    service_name: str,
    event_name: str,
    payload: dict[str, Any],
) -> None:
    if not enabled:
        return
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    safe_service_name = service_name.replace("/", "_")
    file_path = root / f"{timestamp}-{safe_service_name}-{event_name}.json"
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

