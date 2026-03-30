"""Neo4j graph upsert operations for assets and vulnerabilities.

All operations use MERGE for idempotency and include tenantId for tenant isolation.
"""

from __future__ import annotations

from crip_shared.graph import GraphDB
from crip_shared.schemas import Asset, Vulnerability


async def upsert_asset(graph: GraphDB, tenant_id: str, asset: Asset) -> None:
    """Upsert an asset node in Neo4j, scoped to the tenant.

    Uses MERGE on (assetId, tenantId) to ensure idempotency. All properties
    are set on every upsert so the graph reflects the latest connector data.
    """
    cypher = """
    MERGE (a:Asset {assetId: $assetId, tenantId: $tenantId})
    SET a.name = $name,
        a.type = $type,
        a.criticality = $criticality,
        a.businessUnit = $businessUnit,
        a.ipAddress = $ipAddress,
        a.os = $os,
        a.zone = $zone,
        a.edrCoverage = $edrCoverage,
        a.patchLevel = $patchLevel,
        a.lastSeen = datetime($lastSeen)
    """
    await graph.query(cypher, {
        "assetId": asset.asset_id,
        "tenantId": tenant_id,
        "name": asset.name,
        "type": asset.type,
        "criticality": asset.criticality,
        "businessUnit": asset.business_unit,
        "ipAddress": asset.ip_address,
        "os": asset.os,
        "zone": asset.zone,
        "edrCoverage": asset.edr_coverage,
        "patchLevel": asset.patch_level,
        "lastSeen": asset.last_seen.isoformat(),
    })


async def upsert_vulnerability(graph: GraphDB, tenant_id: str, vuln: Vulnerability) -> None:
    """Upsert a vulnerability node in Neo4j.

    Uses MERGE on cveId. Vulnerability nodes are shared across tenants
    (a CVE is a CVE), but relationships to assets are tenant-scoped.
    """
    cypher = """
    MERGE (v:Vulnerability {cveId: $cveId})
    SET v.cvss = $cvss,
        v.epss = $epss,
        v.exploitAvailable = $exploitAvailable,
        v.patchAvailable = $patchAvailable
    """
    await graph.query(cypher, {
        "cveId": vuln.cve_id,
        "cvss": vuln.cvss,
        "epss": vuln.epss,
        "exploitAvailable": vuln.exploit_available,
        "patchAvailable": vuln.patch_available,
    })


async def link_asset_vulnerability(
    graph: GraphDB, tenant_id: str, asset_id: str, cve_id: str
) -> None:
    """Create a HAS_VULN relationship between an asset and a vulnerability.

    The relationship is scoped to the tenant by matching only assets
    that belong to the given tenantId.
    """
    cypher = """
    MATCH (a:Asset {assetId: $assetId, tenantId: $tenantId})
    MATCH (v:Vulnerability {cveId: $cveId})
    MERGE (a)-[:HAS_VULN]->(v)
    """
    await graph.query(cypher, {
        "assetId": asset_id,
        "tenantId": tenant_id,
        "cveId": cve_id,
    })
