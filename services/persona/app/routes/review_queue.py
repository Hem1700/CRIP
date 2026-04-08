"""Review queue for persona updates requiring human approval."""

from __future__ import annotations

from datetime import datetime, timezone

import boto3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/review-queue", tags=["review"])


def _get_review_table(table_name: str = "crip-review-queue"):
    """Return the review queue DynamoDB table, creating it if needed (local dev)."""
    dynamodb = boto3.resource(
        "dynamodb",
        region_name="us-east-1",
        endpoint_url=settings.DYNAMODB_ENDPOINT,
        aws_access_key_id="local",
        aws_secret_access_key="local",
    )
    table = dynamodb.Table(table_name)
    try:
        table.table_status  # noqa: B018
    except dynamodb.meta.client.exceptions.ResourceNotFoundException:
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": "reviewId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "reviewId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
    return table


class RejectRequest(BaseModel):
    reason: str


@router.get("")
async def list_pending_reviews() -> list[dict]:
    """List all pending review items."""
    table = _get_review_table()
    response = table.scan(
        FilterExpression=boto3.dynamodb.conditions.Attr("status").eq("pending"),
    )
    return response.get("Items", [])


@router.post("/{review_id}/approve")
async def approve_review(review_id: str) -> dict:
    """Approve a review item and publish the persona update."""
    table = _get_review_table()
    response = table.get_item(Key={"reviewId": review_id})
    item = response.get("Item")
    if not item:
        raise HTTPException(status_code=404, detail=f"Review item {review_id} not found")
    if item.get("status") != "pending":
        raise HTTPException(status_code=409, detail=f"Review item {review_id} is already {item['status']}")

    now = datetime.now(timezone.utc).isoformat()
    table.update_item(
        Key={"reviewId": review_id},
        UpdateExpression="SET #s = :status, approvedAt = :ts",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":status": "approved", ":ts": now},
    )

    return {"reviewId": review_id, "status": "approved", "approvedAt": now}


@router.post("/{review_id}/reject")
async def reject_review(review_id: str, body: RejectRequest) -> dict:
    """Reject a review item with a reason."""
    table = _get_review_table()
    response = table.get_item(Key={"reviewId": review_id})
    item = response.get("Item")
    if not item:
        raise HTTPException(status_code=404, detail=f"Review item {review_id} not found")
    if item.get("status") != "pending":
        raise HTTPException(status_code=409, detail=f"Review item {review_id} is already {item['status']}")

    now = datetime.now(timezone.utc).isoformat()
    table.update_item(
        Key={"reviewId": review_id},
        UpdateExpression="SET #s = :status, rejectedAt = :ts, rejectReason = :reason",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":status": "rejected",
            ":ts": now,
            ":reason": body.reason,
        },
    )

    return {"reviewId": review_id, "status": "rejected", "reason": body.reason}
