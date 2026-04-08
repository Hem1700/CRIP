"""Report generation and retrieval endpoints."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import boto3
from fastapi import APIRouter, HTTPException, Request

from app.config import settings
from app.metrics.risk_score import compute_risk_score

router = APIRouter(prefix="/reports", tags=["reports"])


def _get_s3_client():
    """Return an S3 client, using LocalStack endpoint in local dev."""
    return boto3.client(
        "s3",
        region_name="us-east-1",
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id="local",
        aws_secret_access_key="local",
    )


def _get_reports_table(table_name: str = "crip-reports"):
    """Return the reports DynamoDB table, creating it if needed (local dev)."""
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
            KeySchema=[{"AttributeName": "reportId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "reportId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
    return table


def _ensure_bucket(s3_client, bucket_name: str) -> None:
    """Create the S3 bucket if it does not exist (local dev only)."""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except s3_client.exceptions.ClientError:
        s3_client.create_bucket(Bucket=bucket_name)


@router.post("/generate")
async def generate_report(request: Request) -> dict:
    """Generate a CISO risk report for the tenant.

    Computes risk score, gathers top findings, and stores the report as JSON in S3.
    """
    tenant_id = request.state.tenant_id
    graph = request.app.state.graph

    report_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    risk_score = await compute_risk_score(tenant_id, graph)

    # Gather top findings
    findings_result = await graph.query(
        """MATCH (a:Asset {tenantId: $tenantId})-[:HAS_VULN]->(v:Vulnerability)
           WITH a, v, (v.cvss * v.epss * a.criticality / 10.0) AS riskScore
           RETURN a.name AS asset, v.cveId AS cve, v.cvss AS cvss,
                  v.patchAvailable AS patchAvailable, riskScore
           ORDER BY riskScore DESC LIMIT 20""",
        {"tenantId": tenant_id},
    )

    asset_count_result = await graph.query(
        "MATCH (a:Asset {tenantId: $tenantId}) RETURN count(a) AS total",
        {"tenantId": tenant_id},
    )
    total_assets = asset_count_result[0]["total"] if asset_count_result else 0

    report_data = {
        "reportId": report_id,
        "tenantId": tenant_id,
        "generatedAt": now.isoformat(),
        "riskScore": risk_score,
        "totalAssets": total_assets,
        "topFindings": findings_result,
        "recommendations": _generate_recommendations(findings_result, risk_score),
    }

    # Store report JSON in S3
    s3 = _get_s3_client()
    _ensure_bucket(s3, settings.S3_BUCKET_REPORTS)
    s3_key = f"reports/{tenant_id}/{report_id}.json"
    s3.put_object(
        Bucket=settings.S3_BUCKET_REPORTS,
        Key=s3_key,
        Body=json.dumps(report_data, default=str),
        ContentType="application/json",
    )

    # Track report metadata in DynamoDB
    table = _get_reports_table()
    table.put_item(Item={
        "reportId": report_id,
        "tenantId": tenant_id,
        "status": "completed",
        "generatedAt": now.isoformat(),
        "s3Key": s3_key,
        "riskScore": str(risk_score),
    })

    return {
        "reportId": report_id,
        "status": "completed",
        "riskScore": risk_score,
    }


@router.get("/{report_id}")
async def get_report(report_id: str, request: Request) -> dict:
    """Return report status and download URL."""
    table = _get_reports_table()
    response = table.get_item(Key={"reportId": report_id})
    item = response.get("Item")
    if not item:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")

    # Generate a presigned URL for the S3 object
    s3 = _get_s3_client()
    download_url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET_REPORTS, "Key": item["s3Key"]},
        ExpiresIn=3600,
    )

    return {
        "reportId": report_id,
        "status": item.get("status", "unknown"),
        "generatedAt": item.get("generatedAt"),
        "riskScore": float(item.get("riskScore", 0)),
        "downloadUrl": download_url,
    }


def _generate_recommendations(findings: list[dict], risk_score: float) -> list[str]:
    """Generate actionable recommendations based on findings and risk score."""
    recs: list[str] = []

    patchable = [f for f in findings if f.get("patchAvailable")]
    if patchable:
        top_cve = patchable[0]["cve"]
        recs.append(
            f"PRIORITY: Patch {top_cve} on {patchable[0]['asset']} immediately — "
            f"exploit available with CVSS {patchable[0]['cvss']}"
        )

    if len(patchable) > 3:
        recs.append(
            f"Schedule patch window for {len(patchable)} vulnerabilities with available patches"
        )

    if risk_score > 700:
        recs.append("CRITICAL: Overall risk score exceeds 700 — escalate to CISO for emergency review")
    elif risk_score > 400:
        recs.append("Elevated risk: review coverage gaps and prioritize EDR deployment to unprotected assets")

    high_cvss = [f for f in findings if f.get("cvss", 0) >= 9.0 and not f.get("patchAvailable")]
    if high_cvss:
        recs.append(
            f"Implement compensating controls for {len(high_cvss)} critical vulnerabilities without patches"
        )

    recs.append("Review attack surface monthly and re-run simulation against top APT personas")

    return recs
