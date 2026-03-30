"""Persona CRUD and simulation trigger endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import boto3
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.config import settings
from app.personas.seed_data import APT_PERSONAS
from app.simulation.kill_chain import KillChainSimulator

router = APIRouter(prefix="/personas", tags=["personas"])


def _get_personas_table(table_name: str = "crip-personas"):
    """Return the personas DynamoDB table, creating it if needed (local dev)."""
    dynamodb = boto3.resource(
        "dynamodb",
        region_name="us-east-1",
        endpoint_url=settings.DYNAMODB_ENDPOINT,
    )
    table = dynamodb.Table(table_name)
    try:
        table.table_status  # noqa: B018
    except dynamodb.meta.client.exceptions.ResourceNotFoundException:
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "groupId", "KeyType": "HASH"},
                {"AttributeName": "version", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "groupId", "AttributeType": "S"},
                {"AttributeName": "version", "AttributeType": "N"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        # Seed initial persona data
        for persona in APT_PERSONAS:
            table.put_item(Item={
                **persona,
                "version": 1,
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "updatedAt": datetime.now(timezone.utc).isoformat(),
            })
    return table


class SimulateRequest(BaseModel):
    tenant_id: str


@router.get("")
async def list_personas() -> list[dict]:
    """List all personas (latest version of each)."""
    table = _get_personas_table()
    response = table.scan()
    items = response.get("Items", [])

    # Group by groupId and take the highest version
    latest: dict[str, dict] = {}
    for item in items:
        gid = item["groupId"]
        ver = int(item.get("version", 1))
        if gid not in latest or ver > int(latest[gid].get("version", 0)):
            latest[gid] = item

    return list(latest.values())


@router.get("/{group_id}")
async def get_persona(group_id: str) -> dict:
    """Get a persona by group ID with all version history."""
    table = _get_personas_table()
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("groupId").eq(group_id),
    )
    items = response.get("Items", [])
    if not items:
        raise HTTPException(status_code=404, detail=f"Persona {group_id} not found")

    items.sort(key=lambda x: int(x.get("version", 1)), reverse=True)
    return {
        "current": items[0],
        "versions": items,
    }


@router.post("/{group_id}/simulate")
async def simulate_persona(group_id: str, body: SimulateRequest, request: Request) -> dict:
    """Trigger a kill-chain simulation for this persona against the tenant's graph.

    Returns a simulation job ID immediately. The simulation runs asynchronously.
    """
    table = _get_personas_table()
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("groupId").eq(group_id),
        ScanIndexForward=False,
        Limit=1,
    )
    items = response.get("Items", [])
    if not items:
        raise HTTPException(status_code=404, detail=f"Persona {group_id} not found")

    persona = items[0]
    graph = request.app.state.graph

    simulator = KillChainSimulator()
    result = await simulator.simulate(
        tenant_id=body.tenant_id,
        persona=persona,
        graph=graph,
    )

    job_id = str(uuid.uuid4())
    return {
        "jobId": job_id,
        "personaId": group_id,
        "personaName": persona["name"],
        "status": "completed",
        "result": result,
    }
