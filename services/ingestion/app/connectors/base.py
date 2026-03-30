"""Abstract base class for all data connectors."""

from __future__ import annotations

from abc import ABC, abstractmethod

from crip_shared.schemas import Asset, IngestionJob, Vulnerability


class BaseConnector(ABC):
    """Interface that every data connector must implement.

    A connector is responsible for pulling asset and vulnerability data from an
    external source (EDR, scanner, CMDB, etc.) and normalizing it into CRIP schemas.
    """

    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = tenant_id

    @abstractmethod
    def validate_connection(self) -> bool:
        """Test that the external source is reachable and credentials are valid."""
        ...

    @abstractmethod
    def fetch_assets(self) -> list[Asset]:
        """Pull all assets from the source and normalize to the Asset schema."""
        ...

    @abstractmethod
    def fetch_vulnerabilities(self) -> list[Vulnerability]:
        """Pull all vulnerabilities from the source and normalize to the Vulnerability schema."""
        ...

    @abstractmethod
    def run(self) -> IngestionJob:
        """Execute a full ingestion cycle and return the job result."""
        ...
