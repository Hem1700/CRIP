"""Synchronous query endpoint for the RAG pipeline."""

from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, Request
from pydantic import BaseModel

from crip_shared.schemas import ApiResponse, ResponseMeta

from app.config import settings
from app.llm.client import get_llm_client
from app.rag.pipeline import RAGPipeline

router = APIRouter(prefix="/query", tags=["reasoning"])


class QueryRequest(BaseModel):
    question: str
    tenant_id: str
    session_id: str


class QueryResult(BaseModel):
    answer: str
    confidence: float
    citations: list[str]
    intent: str


@router.post("/sync")
async def query_sync(body: QueryRequest, request: Request) -> ApiResponse[QueryResult]:
    """Run the full RAG pipeline synchronously and return the complete answer."""
    start = time.perf_counter()
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    graph = request.app.state.graph
    llm_client = get_llm_client(settings)

    pipeline = RAGPipeline(
        graph=graph,
        llm_client=llm_client,
        model=settings.LLM_MODEL,
        max_tokens=settings.MAX_TOKENS,
    )

    result = await pipeline.run_sync(
        question=body.question,
        tenant_id=body.tenant_id,
        session_id=body.session_id,
    )

    duration_ms = (time.perf_counter() - start) * 1000

    return ApiResponse(
        data=QueryResult(
            answer=result["answer"],
            confidence=result["confidence"],
            citations=result["citations"],
            intent=result["intent"],
        ),
        meta=ResponseMeta(
            requestId=request_id,
            tenantId=body.tenant_id,
            durationMs=round(duration_ms, 1),
            confidence=result["confidence"],
        ),
    )
