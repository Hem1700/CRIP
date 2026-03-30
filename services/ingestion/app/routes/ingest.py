"""Ingestion trigger and status endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import boto3
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from crip_shared.schemas import IngestionJob

from app.config import settings
from app.connectors.mock import MockConnector
from app.graph.upsert import link_asset_vulnerability, upsert_asset, upsert_vulnerability

router = APIRouter(prefix="/ingest", tags=["ingestion"])

CONNECTOR_REGISTRY: dict[str, type] = {
    "mock": MockConnector,
}


def _get_dynamodb_table(table_name: str = "crip-ingestion-jobs"):
    """Return a DynamoDB Table resource, using the local endpoint in dev."""
    dynamodb = boto3.resource(
        "dynamodb",
        region_name=settings.AWS_REGION,
        endpoint_url=settings.DYNAMODB_ENDPOINT,
    )
    table = dynamodb.Table(table_name)
    # Ensure table exists (local dev only — in prod, CDK creates this)
    try:
        table.table_status  # noqa: B018  — triggers DescribeTable
    except dynamodb.meta.client.exceptions.ResourceNotFoundException:
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": "jobId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "jobId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
    return table


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

    job = IngestionJob(
        jobId=job_id,
        tenantId=body.tenant_id,
        connectorType=body.connector_type,
        status="running",
        startedAt=now,
    )

    table = _get_dynamodb_table()
    table.put_item(Item={
        "jobId": job.job_id,
        "tenantId": job.tenant_id,
        "connectorType": job.connector_type,
        "status": job.status,
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
    except Exception as exc:
        error_list.append(str(exc))
        status = "failed"

    completed_at = datetime.now(timezone.utc)
    table.update_item(
        Key={"jobId": job_id},
        UpdateExpression="SET #s = :status, completedAt = :completed, assetCount = :ac, errorCount = :ec, errors = :errs",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":status": status,
            ":completed": completed_at.isoformat(),
            ":ac": asset_count,
            ":ec": len(error_list),
            ":errs": error_list,
        },
    )

    return {
        "jobId": job_id,
        "status": status,
        "assetCount": asset_count,
        "errorCount": len(error_list),
    }


@router.get("/status/{job_id}")
async def get_job_status(job_id: str) -> dict:
    """Return the status of an ingestion job."""
    table = _get_dynamodb_table()
    response = table.get_item(Key={"jobId": job_id})
    item = response.get("Item")
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
