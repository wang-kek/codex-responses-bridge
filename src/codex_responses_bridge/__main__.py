from __future__ import annotations

import asyncio
import logging

import uvicorn

from .app import create_app
from .config import load_runtime_services
from .logging_utils import configure_logging


logger = logging.getLogger("codex_responses_bridge.bootstrap")


async def run_service(service) -> None:
    app = create_app(service)
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host=service.host,
            port=service.port,
            log_level="info",
        )
    )
    logger.info(
        "starting service name=%s host=%s port=%s text_provider=%s multimodal_provider=%s",
        service.name,
        service.host,
        service.port,
        service.text_upstream.provider,
        service.multimodal_upstream.provider if service.multimodal_upstream else None,
    )
    await server.serve()


async def async_main() -> None:
    configure_logging()
    services = load_runtime_services()
    if len(services) == 1:
        await run_service(services[0])
        return
    await asyncio.gather(*(run_service(service) for service in services))


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
