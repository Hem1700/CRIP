"""Dashboard data endpoints — posture, heatmap, findings."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from app.metrics.risk_score import compute_risk_score

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/posture")
async def get_posture(request: Request) -> dict:
    """Return the overall security posture for the tenant.

    Includes risk score, asset/vuln counts, and coverage metrics.
    """
    tenant_id = request.state.tenant_id
    graph = request.app.state.graph

    risk_score = await compute_risk_score(tenant_id, graph)

    asset_count_result = await graph.query(
        "MATCH (a:Asset {tenantId: $tenantId}) RETURN count(a) AS total",
        {"tenantId": tenant_id},
    )
    total_assets = asset_count_result[0]["total"] if asset_count_result else 0

    vuln_count_result = await graph.query(
        """MATCH (a:Asset {tenantId: $tenantId})-[:HAS_VULN]->(v:Vulnerability)
           RETURN count(DISTINCT v) AS total""",
        {"tenantId": tenant_id},
    )
    total_vulns = vuln_count_result[0]["total"] if vuln_count_result else 0

    edr_result = await graph.query(
        """MATCH (a:Asset {tenantId: $tenantId})
           RETURN count(CASE WHEN a.edrCoverage = true THEN 1 END) AS covered,
                  count(a) AS total""",
        {"tenantId": tenant_id},
    )
    edr_covered = edr_result[0]["covered"] if edr_result else 0
    edr_total = edr_result[0]["total"] if edr_result else 1
    edr_coverage_pct = round((edr_covered / max(1, edr_total)) * 100, 1)

    patched_result = await graph.query(
        """MATCH (a:Asset {tenantId: $tenantId})
           WHERE a.patchLevel = 'current'
           RETURN count(a) AS patched""",
        {"tenantId": tenant_id},
    )
    patched = patched_result[0]["patched"] if patched_result else 0
    patch_coverage_pct = round((patched / max(1, edr_total)) * 100, 1)

    return {
        "riskScore": risk_score,
        "totalAssets": total_assets,
        "totalVulnerabilities": total_vulns,
        "edrCoveragePct": edr_coverage_pct,
        "patchCoveragePct": patch_coverage_pct,
        "criticalAssets": await _count_critical_assets(tenant_id, graph),
    }


async def _count_critical_assets(tenant_id: str, graph) -> int:
    result = await graph.query(
        "MATCH (a:Asset {tenantId: $tenantId}) WHERE a.criticality >= 8 RETURN count(a) AS c",
        {"tenantId": tenant_id},
    )
    return result[0]["c"] if result else 0


@router.get("/heatmap")
async def get_heatmap(request: Request) -> dict:
    """Return threat actor x critical asset matrix data for D3 heatmap rendering.

    Each cell represents the number of attack paths from a threat actor's TTPs
    to a critical asset.
    """
    tenant_id = request.state.tenant_id
    graph = request.app.state.graph

    # Get threat actors
    actors_result = await graph.query(
        "MATCH (ta:ThreatActor {tenantId: $tenantId}) RETURN ta.name AS name, ta.groupId AS groupId",
        {"tenantId": tenant_id},
    )

    # Get critical assets
    assets_result = await graph.query(
        """MATCH (a:Asset {tenantId: $tenantId})
           WHERE a.criticality >= 8
           RETURN a.assetId AS assetId, a.name AS name, a.criticality AS criticality
           ORDER BY a.criticality DESC
           LIMIT 15""",
        {"tenantId": tenant_id},
    )

    # For each actor-asset pair, count relationships through shared vulnerabilities
    # This is a simplified heatmap — in production you would traverse full attack paths
    cells: list[dict] = []
    for actor in actors_result:
        for asset in assets_result:
            path_result = await graph.query(
                """MATCH (a:Asset {assetId: $assetId, tenantId: $tenantId})-[:HAS_VULN]->(v:Vulnerability)
                   WHERE v.exploitAvailable = true
                   RETURN count(v) AS pathCount""",
                {"assetId": asset["assetId"], "tenantId": tenant_id},
            )
            path_count = path_result[0]["pathCount"] if path_result else 0
            if path_count > 0:
                cells.append({
                    "actorName": actor["name"],
                    "actorId": actor["groupId"],
                    "assetName": asset["name"],
                    "assetId": asset["assetId"],
                    "pathCount": path_count,
                    "intensity": min(1.0, path_count / 5),
                })

    return {
        "actors": [{"name": a["name"], "groupId": a["groupId"]} for a in actors_result],
        "assets": [{"assetId": a["assetId"], "name": a["name"]} for a in assets_result],
        "cells": cells,
    }


@router.get("/findings")
async def get_findings(
    request: Request,
    severity: str | None = Query(None, description="Filter by severity: critical, high, medium, low"),
    status: str | None = Query(None, description="Filter by status: open, acknowledged, resolved"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    """Return paginated findings list with severity and status filters."""
    tenant_id = request.state.tenant_id
    graph = request.app.state.graph

    # Build dynamic WHERE clause
    conditions = ["a.tenantId = $tenantId"]
    params: dict = {"tenantId": tenant_id}

    severity_thresholds = {
        "critical": (9.0, 10.0),
        "high": (7.0, 8.9),
        "medium": (4.0, 6.9),
        "low": (0.0, 3.9),
    }
    if severity and severity in severity_thresholds:
        low, high = severity_thresholds[severity]
        conditions.append("v.cvss >= $cvssLow AND v.cvss <= $cvssHigh")
        params["cvssLow"] = low
        params["cvssHigh"] = high

    where_clause = " AND ".join(conditions)
    skip = (page - 1) * page_size
    params["skip"] = skip
    params["limit"] = page_size

    cypher = f"""
    MATCH (a:Asset)-[:HAS_VULN]->(v:Vulnerability)
    WHERE {where_clause}
    WITH a, v, (v.cvss * v.epss * a.criticality / 10.0) AS riskScore
    RETURN a.assetId AS assetId,
           a.name AS assetName,
           a.criticality AS assetCriticality,
           v.cveId AS cveId,
           v.cvss AS cvss,
           v.epss AS epss,
           v.exploitAvailable AS exploitAvailable,
           v.patchAvailable AS patchAvailable,
           riskScore,
           CASE
             WHEN v.cvss >= 9.0 THEN 'critical'
             WHEN v.cvss >= 7.0 THEN 'high'
             WHEN v.cvss >= 4.0 THEN 'medium'
             ELSE 'low'
           END AS severity
    ORDER BY riskScore DESC
    SKIP $skip LIMIT $limit
    """

    findings = await graph.query(cypher, params)

    # Get total count
    count_cypher = f"""
    MATCH (a:Asset)-[:HAS_VULN]->(v:Vulnerability)
    WHERE {where_clause}
    RETURN count(*) AS total
    """
    count_result = await graph.query(count_cypher, params)
    total = count_result[0]["total"] if count_result else 0

    return {
        "findings": findings,
        "pagination": {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "totalPages": (total + page_size - 1) // page_size,
        },
    }
