import pytest

from tests.conftest import TEST_USER_EMAIL, TEST_USER_PASSWORD


@pytest.mark.asyncio
async def test_not_found_returns_structured_error(client, db_session):
    """404 on nonexistent document returns structured error JSON."""
    resp = await client.get("/api/documents/nonexistent-id")
    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data
    assert data["detail"]["code"] == "NOT_FOUND"
    assert "message" in data["detail"]


@pytest.mark.asyncio
async def test_duplicate_email_returns_conflict_error(client, db_session):
    """409 on duplicate email registration returns structured error."""
    resp = await client.post(
        "/api/auth/register",
        json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "name": "Dup User",
        },
    )
    assert resp.status_code == 409
    data = resp.json()
    assert data["detail"]["code"] == "CONFLICT"
    assert "message" in data["detail"]


@pytest.mark.asyncio
async def test_weak_password_returns_validation_error(unauth_client, db_session):
    """422 on weak password returns structured error."""
    resp = await unauth_client.post(
        "/api/auth/register",
        json={"email": "weak@example.com", "password": "short", "name": "Weak"},
    )
    assert resp.status_code == 422
    data = resp.json()
    assert data["detail"]["code"] == "VALIDATION_ERROR"
    assert "message" in data["detail"]


@pytest.mark.asyncio
async def test_rate_limit_returns_structured_error(client, db_session):
    """429 rate limit returns structured error."""
    from app.services.rate_limiter import chat_rate_limiter

    original_max = chat_rate_limiter.max_requests
    chat_rate_limiter.max_requests = 0  # Force rate limit

    try:
        resp = await client.post(
            "/api/chat",
            json={
                "message": "test",
                "document_ids": ["doc1"],
            },
        )
        assert resp.status_code == 429
        data = resp.json()
        assert data["detail"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert "message" in data["detail"]
    finally:
        chat_rate_limiter.max_requests = original_max
        chat_rate_limiter._requests.clear()


@pytest.mark.asyncio
async def test_responses_have_request_id_header(client, db_session):
    """All responses include X-Request-ID header."""
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert "x-request-id" in resp.headers
    # Verify it looks like a UUID
    request_id = resp.headers["x-request-id"]
    assert len(request_id) == 36
    assert request_id.count("-") == 4
