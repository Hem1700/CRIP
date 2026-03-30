"""Reasoning service — RAG pipeline with Claude for cyber risk analysis."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from crip_shared.graph import GraphDB
from crip_shared.middleware import RequestLoggingMiddleware, TenantMiddleware

from app.config import settings
from app.routes.query import router as query_router
from app.routes.ws import router as ws_router

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Connect Neo4j on startup, disconnect on shutdown."""
    graph = GraphDB(
        uri=settings.NEO4J_URI,
        username=settings.NEO4J_USERNAME,
        password=settings.NEO4J_PASSWORD,
        database=settings.NEO4J_DATABASE,
    )
    await graph.connect()
    app.state.graph = graph
    logger.info("Reasoning service started")
    yield
    await graph.close()
    logger.info("Reasoning service stopped")


app = FastAPI(
    title="CRIP Reasoning Service",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TenantMiddleware)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(query_router)
app.include_router(ws_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "reasoning"}
