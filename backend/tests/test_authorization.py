import pytest


@pytest.mark.asyncio
async def test_user_b_cannot_see_user_a_documents(client, unauth_client, upload_dir, db_session):
    """User A uploads a document; User B cannot see it."""
    # User A uploads
    import io

    pdf_content = b"%PDF-1.4 fake content"
    file = io.BytesIO(pdf_content)
    resp = await client.post(
        "/api/documents/upload",
        files={"file": ("test.pdf", file, "application/pdf")},
    )
    assert resp.status_code == 201
    doc_id = resp.json()["id"]

    # Register User B
    resp_b = await unauth_client.post(
        "/api/auth/register",
        json={"email": "userb@example.com", "password": "password123", "name": "User B"},
    )
    assert resp_b.status_code == 201
    unauth_client.cookies.update(resp_b.cookies)

    # User B lists documents — should be empty
    list_resp = await unauth_client.get("/api/documents")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 0

    # User B tries to get User A's document — 404
    get_resp = await unauth_client.get(f"/api/documents/{doc_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_user_b_cannot_delete_user_a_document(
    client, unauth_client, upload_dir, db_session
):
    """User B cannot delete User A's document."""
    import io

    pdf_content = b"%PDF-1.4 fake content"
    file = io.BytesIO(pdf_content)
    resp = await client.post(
        "/api/documents/upload",
        files={"file": ("test.pdf", file, "application/pdf")},
    )
    assert resp.status_code == 201
    doc_id = resp.json()["id"]

    # Register User B
    resp_b = await unauth_client.post(
        "/api/auth/register",
        json={"email": "userb2@example.com", "password": "password123", "name": "User B"},
    )
    unauth_client.cookies.update(resp_b.cookies)

    # User B tries to delete — 404
    del_resp = await unauth_client.delete(f"/api/documents/{doc_id}")
    assert del_resp.status_code == 404


@pytest.mark.asyncio
async def test_user_b_cannot_see_user_a_conversations(client, unauth_client, db_session):
    """User B cannot see User A's conversations."""
    from app.models.conversation import Conversation

    # Get user A's id
    me_resp = await client.get("/api/auth/me")
    user_a_id = me_resp.json()["id"]

    # Create a conversation for User A
    conv = Conversation(title="User A conv", user_id=user_a_id)
    db_session.add(conv)
    await db_session.flush()
    await db_session.commit()

    # Register User B
    resp_b = await unauth_client.post(
        "/api/auth/register",
        json={"email": "userb3@example.com", "password": "password123", "name": "User B"},
    )
    unauth_client.cookies.update(resp_b.cookies)

    # User B lists conversations — should be empty
    list_resp = await unauth_client.get("/api/conversations")
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_protected_endpoints_return_401(unauth_client, db_session):
    """All protected endpoints return 401 without auth."""
    endpoints = [
        ("GET", "/api/documents"),
        ("GET", "/api/documents/fake-id"),
        ("GET", "/api/conversations"),
        ("GET", "/api/chunks/fake-id"),
        ("POST", "/api/chat"),
        ("GET", "/api/auth/me"),
    ]
    for method, url in endpoints:
        if method == "GET":
            resp = await unauth_client.get(url)
        else:
            resp = await unauth_client.post(url, json={})
        assert resp.status_code in (401, 422), f"{method} {url} returned {resp.status_code}"
