import uuid

import pytest


@pytest.mark.asyncio
async def test_request_id_header_present(client, db_session):
    """Middleware adds X-Request-ID header to responses."""
    resp = await client.get("/api/health")
    assert "x-request-id" in resp.headers


@pytest.mark.asyncio
async def test_request_id_is_valid_uuid(client, db_session):
    """Correlation ID is a valid UUID4."""
    resp = await client.get("/api/health")
    request_id = resp.headers["x-request-id"]
    # Should not raise
    parsed = uuid.UUID(request_id)
    assert parsed.version == 4


@pytest.mark.asyncio
async def test_middleware_does_not_break_normal_flow(client, db_session):
    """Logging middleware doesn't interfere with normal request processing."""
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data
