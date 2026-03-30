"""Serializes Neo4j query results into token-efficient prompt context."""

from __future__ import annotations


def serialize_graph_context(nodes: list[dict]) -> str:
    """Convert Neo4j result rows into a tagged context string for LLM consumption.

    Each row is tagged with a unique nodeId so the LLM can cite specific evidence.
    The format is designed to be token-efficient while remaining unambiguous.

    Args:
        nodes: List of dicts from Neo4j query results.

    Returns:
        A formatted context string with [NODE:xxx] tags for citation.

    Example output::

        [NODE:0] Asset "prod-web-01" | type=server | zone=dmz | criticality=9.2 | edrCoverage=true
        [NODE:1] Asset "prod-db-master" | type=server | zone=production | criticality=10.0 | edrCoverage=false
    """
    if not nodes:
        return "No graph data found for this query."

    lines: list[str] = []
    for idx, row in enumerate(nodes):
        tag = f"[NODE:{idx}]"
        parts: list[str] = []

        for key, value in row.items():
            if value is None:
                continue
            if isinstance(value, list):
                if not value:
                    continue
                # Nested dicts (e.g., vulnerability lists)
                if isinstance(value[0], dict):
                    nested = "; ".join(
                        ", ".join(f"{k}={v}" for k, v in item.items())
                        for item in value[:5]  # Cap nested items to save tokens
                    )
                    parts.append(f"{key}=[{nested}]")
                else:
                    parts.append(f"{key}={value}")
            elif isinstance(value, float):
                parts.append(f"{key}={value:.2f}")
            else:
                parts.append(f"{key}={value}")

        lines.append(f"{tag} {' | '.join(parts)}")

    return "\n".join(lines)
