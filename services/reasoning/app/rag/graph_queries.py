"""Cypher query templates for each intent type.

All queries include tenantId predicates for tenant isolation.
"""

from __future__ import annotations


def attack_path_query(tenant_id: str, actor: str | None, target_type: str | None) -> tuple[str, dict]:
    """Find attack paths from external-facing assets to critical targets.

    Traverses REACHES relationships up to 5 hops, filtering by actor TTP
    coverage if a specific threat actor is named.
    """
    params: dict = {"tenantId": tenant_id}

    actor_filter = ""
    if actor:
        actor_filter = """
        MATCH (ta:ThreatActor {tenantId: $tenantId})-[:USES]->(ttp:TTP)
        WHERE toLower(ta.name) CONTAINS toLower($actor)
        WITH collect(ttp.techniqueId) AS actorTTPs
        """
        params["actor"] = actor

    target_filter = "a2.criticality >= 8"
    if target_type:
        target_filter = f"a2.criticality >= 8 AND a2.type = $targetType"
        params["targetType"] = target_type

    cypher = f"""
    {actor_filter}
    MATCH path = (a1:Asset {{tenantId: $tenantId}})-[:REACHES*1..5]->(a2:Asset {{tenantId: $tenantId}})
    WHERE a1.zone = 'dmz' AND {target_filter}
    WITH path, a1, a2,
         [r IN relationships(path) | r.via] AS techniques,
         reduce(score = 0.0, n IN nodes(path) | score + n.criticality) AS pathScore
    RETURN a1.name AS source,
           a2.name AS target,
           a2.criticality AS targetCriticality,
           techniques,
           pathScore,
           length(path) AS hops
    ORDER BY pathScore DESC
    LIMIT 20
    """
    return cypher, params


def coverage_gap_query(tenant_id: str) -> tuple[str, dict]:
    """Find assets with no EDR coverage that have exploitable vulnerabilities."""
    cypher = """
    MATCH (a:Asset {tenantId: $tenantId})-[:HAS_VULN]->(v:Vulnerability)
    WHERE a.edrCoverage = false AND v.exploitAvailable = true
    RETURN a.assetId AS assetId,
           a.name AS name,
           a.type AS type,
           a.zone AS zone,
           a.criticality AS criticality,
           a.os AS os,
           a.patchLevel AS patchLevel,
           collect({cveId: v.cveId, cvss: v.cvss, epss: v.epss}) AS vulnerabilities,
           count(v) AS vulnCount
    ORDER BY a.criticality DESC, vulnCount DESC
    LIMIT 25
    """
    return cypher, {"tenantId": tenant_id}


def remediation_query(tenant_id: str) -> tuple[str, dict]:
    """Find top findings ranked by composite risk score (CVSS * EPSS * asset criticality)."""
    cypher = """
    MATCH (a:Asset {tenantId: $tenantId})-[:HAS_VULN]->(v:Vulnerability)
    WHERE v.patchAvailable = true
    WITH a, v, (v.cvss * v.epss * a.criticality / 10.0) AS riskScore
    RETURN a.assetId AS assetId,
           a.name AS assetName,
           a.criticality AS assetCriticality,
           v.cveId AS cveId,
           v.cvss AS cvss,
           v.epss AS epss,
           v.patchAvailable AS patchAvailable,
           riskScore
    ORDER BY riskScore DESC
    LIMIT 30
    """
    return cypher, {"tenantId": tenant_id}


def general_query(tenant_id: str, keywords: list[str] | None = None) -> tuple[str, dict]:
    """Broad asset search, optionally filtered by keyword match on name or type."""
    params: dict = {"tenantId": tenant_id}

    keyword_filter = ""
    if keywords:
        conditions = " OR ".join(
            f"toLower(a.name) CONTAINS toLower($kw{i})"
            for i in range(len(keywords))
        )
        keyword_filter = f"AND ({conditions})"
        for i, kw in enumerate(keywords):
            params[f"kw{i}"] = kw

    cypher = f"""
    MATCH (a:Asset {{tenantId: $tenantId}})
    WHERE true {keyword_filter}
    OPTIONAL MATCH (a)-[:HAS_VULN]->(v:Vulnerability)
    RETURN a.assetId AS assetId,
           a.name AS name,
           a.type AS type,
           a.zone AS zone,
           a.criticality AS criticality,
           a.edrCoverage AS edrCoverage,
           a.os AS os,
           count(v) AS vulnCount
    ORDER BY a.criticality DESC
    LIMIT 50
    """
    return cypher, params
