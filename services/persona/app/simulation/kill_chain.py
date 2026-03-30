"""Kill-chain simulation engine.

Simulates an APT persona's TTPs against a tenant's asset graph to identify
which attack paths are viable and which assets are most at risk.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from crip_shared.graph import GraphDB

logger = logging.getLogger(__name__)


@dataclass
class AttackStep:
    """A single step in a simulated attack path."""

    phase: str
    technique_id: str
    technique_name: str
    target_asset_id: str
    target_asset_name: str
    success_probability: float
    notes: str


@dataclass
class SimulationResult:
    """Result of a kill-chain simulation."""

    persona_name: str
    persona_id: str
    tenant_id: str
    total_assets_scanned: int
    vulnerable_assets: int
    attack_paths: list[list[AttackStep]] = field(default_factory=list)
    risk_score: float = 0.0
    summary: str = ""


# Map ATT&CK phases to Cypher conditions that identify vulnerable assets
_PHASE_QUERIES: dict[str, str] = {
    "initial-access": """
        MATCH (a:Asset {tenantId: $tenantId})
        WHERE a.zone = 'dmz' AND a.patchLevel <> 'current'
        RETURN a.assetId AS assetId, a.name AS name, a.criticality AS criticality,
               a.zone AS zone, a.edrCoverage AS edr
        LIMIT 10
    """,
    "execution": """
        MATCH (a:Asset {tenantId: $tenantId})-[:HAS_VULN]->(v:Vulnerability)
        WHERE v.exploitAvailable = true AND v.cvss >= 8.0
        RETURN a.assetId AS assetId, a.name AS name, a.criticality AS criticality,
               v.cveId AS cveId, v.cvss AS cvss
        LIMIT 10
    """,
    "persistence": """
        MATCH (a:Asset {tenantId: $tenantId})
        WHERE a.edrCoverage = false
        RETURN a.assetId AS assetId, a.name AS name, a.criticality AS criticality,
               a.os AS os, a.zone AS zone
        LIMIT 10
    """,
    "lateral-movement": """
        MATCH (a:Asset {tenantId: $tenantId})
        WHERE a.zone = 'internal' OR a.zone = 'production'
        OPTIONAL MATCH (a)-[:HAS_VULN]->(v:Vulnerability)
        WHERE v.exploitAvailable = true
        RETURN a.assetId AS assetId, a.name AS name, a.criticality AS criticality,
               a.zone AS zone, count(v) AS vulnCount
        ORDER BY vulnCount DESC
        LIMIT 10
    """,
    "exfiltration": """
        MATCH (a:Asset {tenantId: $tenantId})
        WHERE a.criticality >= 8
        OPTIONAL MATCH (a)-[:HAS_VULN]->(v:Vulnerability)
        RETURN a.assetId AS assetId, a.name AS name, a.criticality AS criticality,
               a.type AS type, count(v) AS vulnCount
        ORDER BY a.criticality DESC
        LIMIT 10
    """,
}

# Map ATT&CK technique IDs to kill-chain phases
_TECHNIQUE_PHASE_MAP: dict[str, str] = {
    "T1566": "initial-access",
    "T1190": "initial-access",
    "T1133": "initial-access",
    "T1199": "initial-access",
    "T1059": "execution",
    "T1053": "execution",
    "T1569": "execution",
    "T1218": "execution",
    "T1547": "persistence",
    "T1078": "persistence",
    "T1505": "persistence",
    "T1136": "persistence",
    "T1027": "defense-evasion",
    "T1036": "defense-evasion",
    "T1070": "defense-evasion",
    "T1562": "defense-evasion",
    "T1556": "defense-evasion",
    "T1003": "credential-access",
    "T1110": "credential-access",
    "T1539": "credential-access",
    "T1621": "credential-access",
    "T1021": "lateral-movement",
    "T1570": "lateral-movement",
    "T1046": "lateral-movement",
    "T1069": "lateral-movement",
    "T1005": "exfiltration",
    "T1041": "exfiltration",
    "T1048": "exfiltration",
    "T1567": "exfiltration",
    "T1114": "exfiltration",
    "T1560": "exfiltration",
    "T1486": "impact",
    "T1489": "impact",
    "T1490": "impact",
    "T1498": "impact",
    "T1561": "impact",
    "T1565": "impact",
}


def _get_phase_for_technique(technique_id: str) -> str:
    """Resolve the kill-chain phase for a technique ID, handling sub-techniques."""
    # Try full ID first (e.g., T1566.001), then parent (e.g., T1566)
    parent = technique_id.split(".")[0]
    return _TECHNIQUE_PHASE_MAP.get(parent, "execution")


class KillChainSimulator:
    """Simulates an APT persona's kill chain against a tenant's asset graph."""

    async def simulate(
        self,
        tenant_id: str,
        persona: dict,
        graph: GraphDB,
    ) -> dict:
        """Run a kill-chain simulation.

        For each TTP in the persona's repertoire:
        1. Determine which kill-chain phase the TTP belongs to.
        2. Query the graph for assets vulnerable to that phase.
        3. Score the success probability based on asset defenses.
        4. Build ranked attack paths.

        Args:
            tenant_id: The tenant to simulate against.
            persona: The persona dict (from seed_data or DynamoDB).
            graph: Neo4j connection.

        Returns:
            Dict with attack paths, risk score, and summary.
        """
        ttps = persona.get("signatureTTPs", [])
        all_steps: dict[str, list[AttackStep]] = {}
        vulnerable_asset_ids: set[str] = set()

        # Count total assets
        total_result = await graph.query(
            "MATCH (a:Asset {tenantId: $tenantId}) RETURN count(a) AS total",
            {"tenantId": tenant_id},
        )
        total_assets = total_result[0]["total"] if total_result else 0

        for ttp in ttps:
            technique_id = ttp["techniqueId"]
            technique_name = ttp["name"]
            phase = _get_phase_for_technique(technique_id)

            # Find the matching query for this phase, defaulting to execution
            query_key = phase if phase in _PHASE_QUERIES else "execution"
            cypher = _PHASE_QUERIES[query_key]

            try:
                results = await graph.query(cypher, {"tenantId": tenant_id})
            except Exception as exc:
                logger.warning("Query failed for %s: %s", technique_id, exc)
                continue

            for row in results:
                asset_id = row.get("assetId", "unknown")
                asset_name = row.get("name", "unknown")
                criticality = float(row.get("criticality", 5))
                has_edr = row.get("edr", True)

                # Success probability: higher for unpatched, no-EDR, high-criticality targets
                base_prob = 0.5
                if not has_edr:
                    base_prob += 0.2
                if criticality >= 8:
                    base_prob += 0.1
                vuln_count = row.get("vulnCount", 0)
                if isinstance(vuln_count, int) and vuln_count > 0:
                    base_prob += min(0.2, vuln_count * 0.05)

                success_prob = min(0.95, base_prob)

                step = AttackStep(
                    phase=phase,
                    technique_id=technique_id,
                    technique_name=technique_name,
                    target_asset_id=asset_id,
                    target_asset_name=asset_name,
                    success_probability=round(success_prob, 2),
                    notes=f"Phase: {phase}, Criticality: {criticality}",
                )

                all_steps.setdefault(phase, []).append(step)
                vulnerable_asset_ids.add(asset_id)

        # Build attack paths: one path per initial-access entry point
        attack_paths: list[list[dict]] = []
        initial_steps = all_steps.get("initial-access", [])
        for entry in initial_steps[:5]:  # Top 5 entry points
            path: list[dict] = [_step_to_dict(entry)]
            # Chain through phases
            for phase in ["execution", "persistence", "lateral-movement", "exfiltration"]:
                phase_steps = all_steps.get(phase, [])
                if phase_steps:
                    path.append(_step_to_dict(phase_steps[0]))
            attack_paths.append(path)

        # Compute overall risk score (0-100)
        if total_assets == 0:
            risk_score = 0.0
        else:
            coverage = len(vulnerable_asset_ids) / total_assets
            avg_prob = (
                sum(s.success_probability for steps in all_steps.values() for s in steps)
                / max(1, sum(len(s) for s in all_steps.values()))
            )
            risk_score = round(coverage * avg_prob * 100, 1)

        summary = (
            f"{persona['name']} simulation found {len(vulnerable_asset_ids)} vulnerable assets "
            f"out of {total_assets} total ({risk_score:.0f}/100 risk score). "
            f"{len(attack_paths)} viable attack paths identified across "
            f"{len(all_steps)} kill-chain phases."
        )

        return {
            "personaName": persona["name"],
            "personaId": persona["groupId"],
            "tenantId": tenant_id,
            "totalAssetsScanned": total_assets,
            "vulnerableAssets": len(vulnerable_asset_ids),
            "attackPaths": attack_paths,
            "riskScore": risk_score,
            "summary": summary,
        }


def _step_to_dict(step: AttackStep) -> dict:
    """Convert an AttackStep to a serializable dict."""
    return {
        "phase": step.phase,
        "techniqueId": step.technique_id,
        "techniqueName": step.technique_name,
        "targetAssetId": step.target_asset_id,
        "targetAssetName": step.target_asset_name,
        "successProbability": step.success_probability,
        "notes": step.notes,
    }
