"""Tests for conversation CRUD endpoints."""

from httpx import AsyncClient


async def test_list_conversations_empty(client: AsyncClient):
    resp = await client.get("/api/conversations")
    assert resp.status_code == 200
    data = resp.json()
    assert data["conversations"] == []
    assert data["total"] == 0


async def test_list_conversations(client: AsyncClient, conversation_with_messages):
    resp = await client.get("/api/conversations")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    conv = data["conversations"][0]
    assert conv["title"] == "Test conversation"
    assert "id" in conv
    assert "created_at" in conv
    assert "updated_at" in conv


async def test_get_conversation(client: AsyncClient, conversation_with_messages):
    conv_id = conversation_with_messages.id
    resp = await client.get(f"/api/conversations/{conv_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == conv_id
    assert data["title"] == "Test conversation"
    assert len(data["messages"]) == 2
    assert data["messages"][0]["role"] == "user"
    assert data["messages"][0]["content"] == "Hello"
    assert data["messages"][1]["role"] == "assistant"
    assert data["messages"][1]["content"] == "Hi there!"


async def test_get_conversation_not_found(client: AsyncClient):
    resp = await client.get("/api/conversations/nonexistent-id")
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "NOT_FOUND"


async def test_delete_conversation(client: AsyncClient, conversation_with_messages):
    conv_id = conversation_with_messages.id
    resp = await client.delete(f"/api/conversations/{conv_id}")
    assert resp.status_code == 204

    # Verify it's gone
    resp = await client.get(f"/api/conversations/{conv_id}")
    assert resp.status_code == 404


async def test_delete_conversation_not_found(client: AsyncClient):
    resp = await client.delete("/api/conversations/nonexistent-id")
    assert resp.status_code == 404
