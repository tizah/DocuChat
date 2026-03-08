import pytest

from tests.conftest import TEST_USER_EMAIL, TEST_USER_PASSWORD


@pytest.mark.asyncio
async def test_register_success(unauth_client, db_session):
    resp = await unauth_client.post(
        "/api/auth/register",
        json={"email": "new@example.com", "password": "password123", "name": "New User"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert data["name"] == "New User"
    assert "id" in data
    # Should set cookies
    assert "access_token" in resp.cookies


@pytest.mark.asyncio
async def test_register_duplicate_email(client, db_session):
    resp = await client.post(
        "/api/auth/register",
        json={"email": TEST_USER_EMAIL, "password": "password123", "name": "Dup User"},
    )
    assert resp.status_code == 409
    data = resp.json()
    assert data["detail"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_register_weak_password(unauth_client, db_session):
    resp = await unauth_client.post(
        "/api/auth/register",
        json={"email": "weak@example.com", "password": "short", "name": "Weak"},
    )
    assert resp.status_code == 422
    data = resp.json()
    assert data["detail"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_login_success(client, db_session):
    resp = await client.post(
        "/api/auth/login",
        json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == TEST_USER_EMAIL
    assert "access_token" in resp.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client, db_session):
    resp = await client.post(
        "/api/auth/login",
        json={"email": TEST_USER_EMAIL, "password": "wrongpassword"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_email(unauth_client, db_session):
    resp = await unauth_client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "password123"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client, db_session):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == TEST_USER_EMAIL
    assert data["name"] == "Test User"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(unauth_client, db_session):
    resp = await unauth_client.get("/api/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout(client, db_session):
    resp = await client.post("/api/auth/logout")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Logged out"


@pytest.mark.asyncio
async def test_refresh_rotates_tokens(client, db_session):
    # Login to get fresh tokens
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD},
    )
    assert login_resp.status_code == 200
    client.cookies.update(login_resp.cookies)

    # Refresh
    refresh_resp = await client.post("/api/auth/refresh")
    assert refresh_resp.status_code == 200
    assert refresh_resp.json()["message"] == "Tokens refreshed"
