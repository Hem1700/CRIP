"""Neo4j connection helper with async support and context management."""

from __future__ import annotations

import logging
from types import TracebackType

from neo4j import AsyncGraphDatabase, AsyncDriver

logger = logging.getLogger(__name__)


class GraphDB:
    """Async Neo4j client wrapper.

    Usage::

        async with GraphDB("bolt://localhost:7687", "neo4j", "password") as db:
            results = await db.query("MATCH (n:Asset) RETURN n LIMIT 10")
    """

    def __init__(
        self,
        uri: str,
        username: str,
        password: str,
        database: str = "neo4j",
    ) -> None:
        self._uri = uri
        self._username = username
        self._password = password
        self._database = database
        self._driver: AsyncDriver | None = None

    async def connect(self) -> None:
        """Establish the driver connection."""
        self._driver = AsyncGraphDatabase.driver(
            self._uri,
            auth=(self._username, self._password),
        )
        logger.info("Connected to Neo4j at %s", self._uri)

    async def query(self, cypher: str, params: dict | None = None) -> list[dict]:
        """Execute a Cypher query and return results as a list of dicts.

        Args:
            cypher: The Cypher query string.
            params: Optional parameter dict for the query.

        Returns:
            List of record dicts.
        """
        if self._driver is None:
            raise RuntimeError("GraphDB is not connected. Call connect() first.")

        async with self._driver.session(database=self._database) as session:
            result = await session.run(cypher, parameters=params or {})
            records = await result.data()
            return records

    async def close(self) -> None:
        """Close the driver connection."""
        if self._driver is not None:
            await self._driver.close()
            self._driver = None
            logger.info("Disconnected from Neo4j")

    async def __aenter__(self) -> GraphDB:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()
