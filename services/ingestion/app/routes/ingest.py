"""Ingestion trigger and status endpoints."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from crip_shared.schemas import IngestionJob

from app.connectors.mock import MockConnector
from app.graph.upsert import link_asset_vulnerability, upsert_asset, upsert_vulnerability

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingestion"])

CONNECTOR_REGISTRY: dict[str, type] = {
    "mock": MockConnector,
}

# In-memory job store for local dev (replaces DynamoDB when unavailable)
_job_store: dict[str, dict] = {}


def _save_job(job_id: str, data: dict) -> None:
    _job_store[job_id] = data


def _update_job(job_id: str, updates: dict) -> None:
    if job_id in _job_store:
        _job_store[job_id].update(updates)


def _get_job(job_id: str) -> dict | None:
    return _job_store.get(job_id)


class TriggerRequest(BaseModel):
    connector_type: str
    tenant_id: str


class ConnectorInfo(BaseModel):
    name: str
    status: str


@router.post("/trigger")
async def trigger_ingestion(body: TriggerRequest, request: Request) -> dict:
    """Start an ingestion job for the given connector type."""
    if body.connector_type not in CONNECTOR_REGISTRY:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown connector type: {body.connector_type}. Available: {list(CONNECTOR_REGISTRY.keys())}",
        )

    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    _save_job(job_id, {
        "jobId": job_id,
        "tenantId": body.tenant_id,
        "connectorType": body.connector_type,
        "status": "running",
        "startedAt": now.isoformat(),
        "assetCount": 0,
        "errorCount": 0,
        "errors": [],
    })

    # Run the connector
    graph = request.app.state.graph
    connector_cls = CONNECTOR_REGISTRY[body.connector_type]
    connector = connector_cls(tenant_id=body.tenant_id)

    error_list: list[str] = []
    asset_count = 0
    try:
        assets = connector.fetch_assets()
        vulns = connector.fetch_vulnerabilities()

        for asset in assets:
            await upsert_asset(graph, body.tenant_id, asset)
            asset_count += 1

        for vuln in vulns:
            await upsert_vulnerability(graph, body.tenant_id, vuln)

        # Link some assets to vulnerabilities for a realistic graph
        for i, asset in enumerate(assets):
            # Each asset gets a few vulns based on its index
            for vuln in vulns[i % len(vulns) : i % len(vulns) + 3]:
                await link_asset_vulnerability(graph, body.tenant_id, asset.asset_id, vuln.cve_id)

        status = "completed"
        logger.info("Ingestion completed: %d assets ingested", asset_count)
    except Exception as exc:
        logger.exception("Ingestion failed: %s", exc)
        error_list.append(str(exc))
        status = "failed"

    completed_at = datetime.now(timezone.utc)
    _update_job(job_id, {
        "status": status,
        "completedAt": completed_at.isoformat(),
        "assetCount": asset_count,
        "errorCount": len(error_list),
        "errors": error_list,
    })

    return {
        "jobId": job_id,
        "status": status,
        "assetCount": asset_count,
        "errorCount": len(error_list),
    }


@router.get("/status/{job_id}")
async def get_job_status(job_id: str) -> dict:
    """Return the status of an ingestion job."""
    item = _get_job(job_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return item


@router.get("/connectors")
async def list_connectors() -> list[ConnectorInfo]:
    """Return all available connector types."""
    return [
        ConnectorInfo(name=name, status="available")
        for name in CONNECTOR_REGISTRY
    ]
