"""WebSocket endpoint for streaming analyst chat."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from crip_shared.graph import GraphDB

from app.config import settings
from app.llm.client import get_llm_client
from app.rag.pipeline import RAGPipeline

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


def _extract_tenant_id(websocket: WebSocket) -> str | None:
    """Extract tenant ID from query params (JWT or X-Tenant-ID)."""
    # Check for explicit tenant ID query param (local dev)
    tenant_id = websocket.query_params.get("tenantId")
    if tenant_id:
        return tenant_id

    # Check for token query param (production)
    token = websocket.query_params.get("token")
    if token:
        # In production, the API Gateway validates the JWT before it reaches here.
        # For local dev, we just extract the sub claim without verification.
        try:
            from base64 import b64decode

            parts = token.split(".")
            if len(parts) == 3:
                payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
                payload = json.loads(b64decode(payload_b64))
                return payload.get("sub") or payload.get("tenantId")
        except (ValueError, json.JSONDecodeError):
            pass

    return None


@router.websocket("/ws/analyst")
async def analyst_websocket(websocket: WebSocket) -> None:
    """Streaming analyst chat over WebSocket.

    Protocol:
    - Client sends: {"question": "...", "sessionId": "..."}
    - Server streams: {"type": "token", "content": "..."} per token
    - Server finishes: {"type": "done", "confidence": 0.87, "citations": [...]}
    - On error:       {"type": "error", "message": "..."}
    """
    tenant_id = _extract_tenant_id(websocket)
    if not tenant_id:
        await websocket.close(code=4001, reason="Missing tenant identifier")
        return

    await websocket.accept()
    logger.info("WebSocket connected: tenant=%s", tenant_id)

    graph: GraphDB = websocket.app.state.graph
    llm_client = get_llm_client(settings)

    pipeline = RAGPipeline(
        graph=graph,
        llm_client=llm_client,
        model=settings.LLM_MODEL,
        max_tokens=settings.MAX_TOKENS,
    )

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON message",
                })
                continue

            question = message.get("question", "").strip()
            session_id = message.get("sessionId", "default")

            if not question:
                await websocket.send_json({
                    "type": "error",
                    "message": "Empty question",
                })
                continue

            try:
                async for chunk in pipeline.run_streaming(
                    question=question,
                    tenant_id=tenant_id,
                    session_id=session_id,
                ):
                    if chunk["type"] == "token":
                        await websocket.send_json({
                            "type": "token",
                            "content": chunk["content"],
                        })
                    elif chunk["type"] == "done":
                        await websocket.send_json({
                            "type": "done",
                            "confidence": chunk["confidence"],
                            "citations": chunk["citations"],
                        })

            except Exception as exc:
                logger.exception("Pipeline error for tenant=%s", tenant_id)
                await websocket.send_json({
                    "type": "error",
                    "message": f"Pipeline error: {exc}",
                })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: tenant=%s", tenant_id)
    except Exception:
        logger.exception("Unexpected WebSocket error: tenant=%s", tenant_id)
        try:
            await websocket.close(code=1011, reason="Internal error")
        except RuntimeError:
            pass  # Connection already closed
