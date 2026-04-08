"""Risk score computation for the CRIP dashboard."""

from __future__ import annotations


async def compute_risk_score(tenant_id: str, graph) -> float:
    """Compute an aggregate risk score (0–1000) for the tenant.

    Formula: weighted sum of critical vulnerabilities with active exploits,
    normalised against total asset count.
    """
    result = await graph.query(
        """MATCH (a:Asset {tenantId: $tenantId})-[:HAS_VULN]->(v:Vulnerability)
           WHERE v.exploitAvailable = true
           WITH a, v,
                (v.cvss * v.epss * a.criticality / 10.0) AS itemScore
           WITH sum(itemScore) AS rawScore
           MATCH (total:Asset {tenantId: $tenantId})
           WITH rawScore, count(total) AS assetCount
           RETURN CASE WHEN assetCount = 0 THEN 0
                       ELSE round(rawScore / assetCount * 100) END AS score""",
        {"tenantId": tenant_id},
    )
    if result and result[0]["score"] is not None:
        return float(result[0]["score"])

    # Fallback: simpler query
    fallback = await graph.query(
        """MATCH (a:Asset {tenantId: $tenantId})-[:HAS_VULN]->(v:Vulnerability)
           RETURN avg(v.cvss * coalesce(v.epss, 0.5)) AS avg_risk""",
        {"tenantId": tenant_id},
    )
    if fallback and fallback[0]["avg_risk"] is not None:
        return round(float(fallback[0]["avg_risk"]) * 100, 1)
    return 0.0
