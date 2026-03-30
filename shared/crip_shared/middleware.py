"""FastAPI middleware for tenant isolation and request logging."""

from __future__ import annotations

import logging
import time
import uuid
from base64 import b64decode
from json import JSONDecodeError, loads

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)


def _extract_tenant_from_jwt(auth_header: str) -> str | None:
    """Decode the JWT payload (without verification for local dev) and extract sub claim.

    In production, token verification is handled by the API Gateway / Cognito authorizer
    before requests reach the service. This extraction is a convenience for routing.
    """
    try:
        token = auth_header.removeprefix("Bearer ").strip()
        parts = token.split(".")
        if len(parts) != 3:
            return None
        # Pad the base64 payload
        payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
        payload = loads(b64decode(payload_b64))
        return payload.get("sub") or payload.get("tenantId")
    except (ValueError, JSONDecodeError, UnicodeDecodeError):
        return None


class TenantMiddleware(BaseHTTPMiddleware):
    """Extracts tenantId from JWT or X-Tenant-ID header and injects into request state.

    Priority:
    1. Authorization header JWT 'sub' claim
    2. X-Tenant-ID header (local dev convenience)

    Rejects requests without a tenant identifier (except health endpoints).
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip tenant check for health and docs endpoints
        if request.url.path in ("/health", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        tenant_id: str | None = None

        # Try JWT first
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            tenant_id = _extract_tenant_from_jwt(auth_header)

        # Fall back to explicit header (local dev)
        if not tenant_id:
            tenant_id = request.headers.get("x-tenant-id")

        if not tenant_id:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing tenant identifier. Provide Authorization header or X-Tenant-ID."},
            )

        request.state.tenant_id = tenant_id
        request.state.request_id = str(uuid.uuid4())
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every request with method, path, tenantId, duration, and status code."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        tenant_id = getattr(request.state, "tenant_id", "-")
        logger.info(
            "%s %s tenant=%s duration=%.1fms status=%d",
            request.method,
            request.url.path,
            tenant_id,
            duration_ms,
            response.status_code,
        )
        return response
