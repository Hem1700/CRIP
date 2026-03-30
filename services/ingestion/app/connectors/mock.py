"""Mock connector that generates realistic fake data for local development."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from crip_shared.schemas import Asset, IngestionJob, Vulnerability

from app.connectors.base import BaseConnector

_SERVER_NAMES = [
    "prod-web-01", "prod-web-02", "prod-web-03", "prod-api-01", "prod-api-02",
    "prod-db-master", "prod-db-replica-01", "prod-db-replica-02",
    "staging-web-01", "staging-api-01", "staging-db-01",
    "dev-web-01", "dev-api-01", "dev-db-01",
    "ci-runner-01", "ci-runner-02",
    "vpn-gateway-01", "vpn-gateway-02",
    "mail-relay-01", "dns-resolver-01",
    "monitoring-01", "logging-01", "logging-02",
    "bastion-01", "bastion-02",
    "k8s-master-01", "k8s-worker-01", "k8s-worker-02", "k8s-worker-03", "k8s-worker-04",
    "redis-cache-01", "redis-cache-02",
    "mq-broker-01", "mq-broker-02",
    "file-server-01", "backup-server-01",
    "ad-dc-01", "ad-dc-02",
    "siem-collector-01", "siem-indexer-01",
    "proxy-01", "proxy-02",
    "iot-gateway-01", "scada-hmi-01", "scada-plc-bridge-01",
    "erp-app-01", "crm-app-01", "hr-portal-01",
    "dev-laptop-jsmith", "dev-laptop-agarcia",
]

_OS_OPTIONS = [
    "Ubuntu 22.04 LTS", "Ubuntu 24.04 LTS", "RHEL 9.3", "RHEL 8.8",
    "Windows Server 2022", "Windows Server 2019", "CentOS Stream 9",
    "Debian 12", "Amazon Linux 2023", "macOS 14.4",
]

_ZONES = ["dmz", "internal", "production", "staging", "development", "iot", "management"]
_BUSINESS_UNITS = ["Engineering", "IT Operations", "Security", "Finance", "HR", "Executive", "OT"]
_TYPES = ["server", "workstation", "network_device", "iot_device", "virtual_machine", "container_host"]
_PATCH_LEVELS = ["current", "30-days-behind", "60-days-behind", "90-days-behind", "180-days-behind", "unknown"]

_CVES = [
    ("CVE-2024-3094", 10.0, 0.97, True, False),   # xz backdoor
    ("CVE-2024-21762", 9.8, 0.95, True, False),    # FortiOS RCE
    ("CVE-2023-44228", 10.0, 0.98, True, True),    # Log4Shell variant
    ("CVE-2024-1709", 10.0, 0.92, True, False),    # ConnectWise ScreenConnect
    ("CVE-2024-27198", 9.8, 0.89, True, True),     # JetBrains TeamCity
    ("CVE-2023-46805", 8.2, 0.91, True, False),    # Ivanti Connect Secure
    ("CVE-2024-0012", 9.8, 0.85, True, False),     # PAN-OS auth bypass
    ("CVE-2023-34362", 9.8, 0.96, True, True),     # MOVEit SQL injection
    ("CVE-2024-23897", 9.8, 0.78, True, True),     # Jenkins arbitrary file read
    ("CVE-2023-20198", 10.0, 0.93, True, False),   # Cisco IOS XE
    ("CVE-2024-38063", 9.8, 0.72, True, True),     # Windows TCP/IP RCE
    ("CVE-2023-22515", 10.0, 0.88, True, True),    # Atlassian Confluence
    ("CVE-2024-4577", 9.8, 0.81, True, True),      # PHP CGI argument injection
    ("CVE-2023-36884", 8.8, 0.76, True, True),     # Office/Windows HTML RCE
    ("CVE-2024-28986", 9.8, 0.69, True, False),    # SolarWinds WHD
    ("CVE-2023-42793", 9.8, 0.84, True, True),     # TeamCity auth bypass
    ("CVE-2024-21887", 9.1, 0.90, True, False),    # Ivanti command injection
    ("CVE-2023-29357", 9.8, 0.75, True, True),     # SharePoint escalation
    ("CVE-2024-5806", 9.1, 0.67, True, False),     # Progress MOVEit auth bypass
    ("CVE-2023-48788", 9.8, 0.71, True, True),     # FortiClient EMS SQL injection
]


class MockConnector(BaseConnector):
    """Generates realistic synthetic asset and vulnerability data.

    Useful for local development and demo environments.
    """

    def validate_connection(self) -> bool:
        return True

    def fetch_assets(self) -> list[Asset]:
        """Generate 50 realistic assets."""
        assets: list[Asset] = []
        now = datetime.now(timezone.utc)

        for i, name in enumerate(_SERVER_NAMES):
            # Deterministic but varied values based on index
            criticality = round(min(10.0, max(0.0, 3.0 + (i * 1.7 % 8))), 1)
            has_edr = i % 5 != 0  # 80% EDR coverage, 20% gaps
            octets = [10, 0, (i // 256) % 256, i % 256]
            ip_address = ".".join(str(o) for o in octets)

            asset = Asset(
                tenantId=self.tenant_id,
                assetId=f"asset-{i:04d}",
                name=name,
                type=_TYPES[i % len(_TYPES)],
                criticality=criticality,
                businessUnit=_BUSINESS_UNITS[i % len(_BUSINESS_UNITS)],
                ipAddress=ip_address,
                os=_OS_OPTIONS[i % len(_OS_OPTIONS)],
                zone=_ZONES[i % len(_ZONES)],
                edrCoverage=has_edr,
                patchLevel=_PATCH_LEVELS[i % len(_PATCH_LEVELS)],
                lastSeen=now,
            )
            assets.append(asset)

        return assets

    def fetch_vulnerabilities(self) -> list[Vulnerability]:
        """Generate 20 realistic vulnerabilities from known CVEs."""
        vulns: list[Vulnerability] = []
        for cve_id, cvss, epss, exploit, patch in _CVES:
            vuln = Vulnerability(
                cveId=cve_id,
                cvss=cvss,
                epss=epss,
                exploitAvailable=exploit,
                patchAvailable=patch,
            )
            vulns.append(vuln)
        return vulns

    def run(self) -> IngestionJob:
        """Execute a mock ingestion run."""
        assets = self.fetch_assets()
        vulns = self.fetch_vulnerabilities()
        now = datetime.now(timezone.utc)
        return IngestionJob(
            jobId=str(uuid.uuid4()),
            tenantId=self.tenant_id,
            connectorType="mock",
            status="completed",
            startedAt=now,
            completedAt=now,
            assetCount=len(assets),
            errorCount=0,
            errors=[],
        )
