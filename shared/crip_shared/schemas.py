"""Shared Pydantic v2 models for the CRIP platform."""

from datetime import datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Asset(BaseModel):
    """An IT/OT asset within a tenant's environment."""

    tenant_id: str = Field(alias="tenantId")
    asset_id: str = Field(alias="assetId")
    name: str
    type: str
    criticality: float = Field(ge=0, le=10)
    business_unit: str = Field(alias="businessUnit")
    ip_address: str = Field(alias="ipAddress")
    os: str
    zone: str
    edr_coverage: bool = Field(alias="edrCoverage")
    patch_level: str = Field(alias="patchLevel")
    last_seen: datetime = Field(alias="lastSeen")

    model_config = {"populate_by_name": True}


class Vulnerability(BaseModel):
    """A CVE-identified vulnerability."""

    cve_id: str = Field(alias="cveId")
    cvss: float = Field(ge=0, le=10)
    epss: float = Field(ge=0, le=1)
    exploit_available: bool = Field(alias="exploitAvailable")
    patch_available: bool = Field(alias="patchAvailable")

    model_config = {"populate_by_name": True}


class ThreatActor(BaseModel):
    """A known threat actor / APT group."""

    group_id: str = Field(alias="groupId")
    name: str
    target_sectors: list[str] = Field(alias="targetSectors")
    sophistication: str
    last_seen: datetime = Field(alias="lastSeen")

    model_config = {"populate_by_name": True}


class TTP(BaseModel):
    """A MITRE ATT&CK technique."""

    technique_id: str = Field(alias="techniqueId")
    name: str
    phase: str
    platforms: list[str]

    model_config = {"populate_by_name": True}


class ResponseMeta(BaseModel):
    """Metadata attached to every API response."""

    request_id: str = Field(alias="requestId")
    tenant_id: str = Field(alias="tenantId")
    duration_ms: float = Field(alias="durationMs")
    confidence: float | None = None

    model_config = {"populate_by_name": True}


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    data: T
    meta: ResponseMeta
    errors: list[str] = Field(default_factory=list)


class IngestionJob(BaseModel):
    """Tracks an ingestion run."""

    job_id: str = Field(alias="jobId")
    tenant_id: str = Field(alias="tenantId")
    connector_type: str = Field(alias="connectorType")
    status: Literal["pending", "running", "completed", "failed"]
    started_at: datetime | None = Field(default=None, alias="startedAt")
    completed_at: datetime | None = Field(default=None, alias="completedAt")
    asset_count: int = Field(default=0, alias="assetCount")
    error_count: int = Field(default=0, alias="errorCount")
    errors: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}
