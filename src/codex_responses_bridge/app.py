from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from .i18n import translate
from .model_aliases import resolve_model_for_selected_upstream
from .models import ServiceConfig
from .provider_adapters import adapt_openai_chat_payload
from .provider_profiles import build_public_model_entries, sanitize_openai_chat_payload
from .request_capture import capture_protocol_event
from .translators.responses_openai import (
    build_failed_response_event,
    convert_chat_to_responses_payload,
    convert_responses_to_openai_chat,
    has_multimodal_content,
    stream_openai_chat_to_responses,
)
from .upstreams.base import select_upstream
from .upstreams.openai import post_chat_completions, stream_chat_completions

logger = logging.getLogger("codex_responses_bridge")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient()
    try:
        yield
    finally:
        await app.state.http_client.aclose()


def create_app(service: ServiceConfig) -> FastAPI:
    app = FastAPI(title=f"codex-responses-bridge:{service.name}", lifespan=lifespan)
    app.state.service_config = service

    @app.get("/health")
    async def health() -> dict:
        return {
            "ok": True,
            "name": "codex-responses-bridge",
            "service": service.name,
            "protocol_mode": service.protocol_mode,
            "text_provider": service.text_upstream.provider,
            "multimodal_provider": service.multimodal_upstream.provider if service.multimodal_upstream else None,
            "language": service.language,
        }

    @app.get("/v1/models")
    async def models() -> dict:
        return {"object": "list", "data": build_public_model_entries(service)}

    @app.post("/v1/responses")
    async def responses_proxy(request: Request):
        try:
            body = await request.json()
        except Exception:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "message": translate(service.language, "invalid_json"),
                        "type": "invalid_request_error",
                        "code": "invalid_json",
                    }
                },
            )

        multimodal = has_multimodal_content(body.get("input"))
        selected = select_upstream(service, has_multimodal_input=multimodal)
        requested_model = body.get("model")
        resolved_model, source_model = resolve_model_for_selected_upstream(
            service=service,
            upstream=selected.config,
            requested_model=requested_model,
            is_multimodal=multimodal,
        )
        translated_payload = convert_responses_to_openai_chat(body, resolved_model)
        adapted_payload = adapt_openai_chat_payload(
            upstream=selected.config,
            payload=translated_payload,
        )
        upstream_payload, removed_fields = sanitize_openai_chat_payload(
            upstream=selected.config,
            payload=adapted_payload.payload,
            is_multimodal=multimodal,
        )
        removed_fields = [*adapted_payload.changed_fields, *removed_fields]
        response_id = body.get("id") or f"resp_{uuid.uuid4().hex[:12]}"

        capture_protocol_event(
            enabled=service.request_capture_enabled,
            directory=service.request_capture_directory,
            service_name=service.name,
            event_name="incoming-responses",
            payload=body,
        )
        capture_protocol_event(
            enabled=service.request_capture_enabled,
            directory=service.request_capture_directory,
            service_name=service.name,
            event_name="translated-openai-chat",
            payload={"payload": upstream_payload, "removed_fields": removed_fields},
        )

        logger.info(
            "service=%s port=%s provider=%s purpose=%s stream=%s requested_model=%s upstream_model=%s mapping_applied=%s removed_fields=%s",
            service.name,
            service.port,
            selected.config.provider,
            selected.purpose,
            bool(upstream_payload.get("stream")),
            requested_model,
            resolved_model,
            source_model is not None,
            removed_fields,
        )

        if selected.config.protocol_mode != "openai-chat":
            return JSONResponse(
                status_code=501,
                content={
                    "error": {
                        "message": f"{translate(service.language, 'unsupported_protocol_mode')}: {selected.config.protocol_mode}",
                        "type": "not_implemented",
                        "code": "unsupported_protocol_mode",
                    }
                },
            )

        client: httpx.AsyncClient = request.app.state.http_client
        if upstream_payload.get("stream"):
            async def event_stream():
                try:
                    async with stream_chat_completions(client, config=selected.config, payload=upstream_payload) as resp:
                        if resp.status_code >= 400:
                            error_text = (await resp.aread()).decode("utf-8", errors="ignore")
                            capture_protocol_event(
                                enabled=service.request_capture_enabled,
                                directory=service.request_capture_directory,
                                service_name=service.name,
                                event_name="upstream-stream-error",
                                payload={"status_code": resp.status_code, "body": error_text[:4000]},
                            )
                            yield build_failed_response_event(
                                response_id=response_id,
                                model=resolved_model,
                                message=error_text or f"upstream http {resp.status_code}",
                            )
                            return

                        async for chunk in stream_openai_chat_to_responses(
                            resp,
                            response_id=response_id,
                            model=resolved_model,
                            request_max_output_tokens=upstream_payload.get("max_tokens"),
                        ):
                            yield chunk
                except Exception as exc:
                    logger.exception("stream proxy error service=%s", service.name)
                    yield build_failed_response_event(
                        response_id=response_id,
                        model=resolved_model,
                        message=str(exc),
                        error_type="proxy_error",
                    )

            return StreamingResponse(
                event_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )

        try:
            resp = await post_chat_completions(client, config=selected.config, payload=upstream_payload)
        except Exception as exc:
            logger.exception("non-stream proxy error service=%s", service.name)
            return JSONResponse(
                status_code=502,
                content={
                    "error": {
                        "message": str(exc),
                        "type": "proxy_error",
                        "code": "proxy_error",
                    }
                },
            )

        content_type = resp.headers.get("content-type", "application/json")
        response_payload: object
        try:
            response_payload = resp.json()
        except Exception:
            response_payload = {"raw": resp.text}

        capture_protocol_event(
            enabled=service.request_capture_enabled,
            directory=service.request_capture_directory,
            service_name=service.name,
            event_name="upstream-response",
            payload={"status_code": resp.status_code, "body": response_payload},
        )

        if resp.status_code >= 400:
            if isinstance(response_payload, dict):
                return JSONResponse(status_code=resp.status_code, content=response_payload)
            return Response(status_code=resp.status_code, content=resp.text, media_type=content_type)

        if not isinstance(response_payload, dict):
            return JSONResponse(
                status_code=502,
                content={
                    "error": {
                        "message": "upstream returned non-json response",
                        "type": "upstream_error",
                        "code": "invalid_upstream_payload",
                    }
                },
            )

        translated = convert_chat_to_responses_payload(response_payload, resolved_model)
        capture_protocol_event(
            enabled=service.request_capture_enabled,
            directory=service.request_capture_directory,
            service_name=service.name,
            event_name="translated-responses",
            payload=translated,
        )
        return JSONResponse(status_code=200, content=translated)

    @app.get("/")
    async def root() -> dict:
        return {
            "name": "codex-responses-bridge",
            "service": service.name,
            "language": service.language,
            "routes": ["/health", "/v1/models", "/v1/responses"],
        }

    return app
