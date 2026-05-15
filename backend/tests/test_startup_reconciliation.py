"""Startup reconciliation marks stuck documents as failed."""

from unittest.mock import patch

import pytest

from app.main import NON_TERMINAL_DOC_STATUSES, _reconcile_stuck_documents
from app.models.document import Document
from app.models.user import User
from app.services.auth import hash_password


@pytest.fixture
async def user(db_session):
    u = User(email="recon@example.com", hashed_password=hash_password("x"), name="R")
    db_session.add(u)
    await db_session.flush()
    await db_session.commit()
    return u


@pytest.mark.asyncio
async def test_stuck_documents_marked_failed_with_message(db_session, user):
    """Docs in any non-terminal state get flipped to failed with an explanatory message."""
    stuck = [
        Document(user_id=user.id, filename=f"{s}.pdf", file_type="pdf", size_bytes=1, status=s)
        for s in NON_TERMINAL_DOC_STATUSES
    ]
    db_session.add_all(stuck)
    await db_session.flush()
    await db_session.commit()
    stuck_ids = [d.id for d in stuck]

    # _reconcile_stuck_documents opens its own session via async_session(). Point
    # that at the test session so the in-memory test db is what gets reconciled.
    async def _yield_test_session():
        yield db_session

    with patch("app.main.async_session") as mock_factory:
        mock_factory.return_value.__aenter__.return_value = db_session
        mock_factory.return_value.__aexit__.return_value = None
        await _reconcile_stuck_documents()

    for doc_id in stuck_ids:
        await db_session.refresh(next(d for d in stuck if d.id == doc_id))
    for d in stuck:
        assert d.status == "failed"
        assert "interrupted" in (d.error_message or "").lower()


@pytest.mark.asyncio
async def test_terminal_documents_untouched(db_session, user):
    """ready/failed docs are not touched."""
    ready = Document(
        user_id=user.id, filename="r.pdf", file_type="pdf", size_bytes=1, status="ready"
    )
    failed = Document(
        user_id=user.id,
        filename="f.pdf",
        file_type="pdf",
        size_bytes=1,
        status="failed",
        error_message="prior failure reason",
    )
    db_session.add_all([ready, failed])
    await db_session.flush()
    await db_session.commit()

    with patch("app.main.async_session") as mock_factory:
        mock_factory.return_value.__aenter__.return_value = db_session
        mock_factory.return_value.__aexit__.return_value = None
        await _reconcile_stuck_documents()

    await db_session.refresh(ready)
    await db_session.refresh(failed)
    assert ready.status == "ready"
    assert failed.status == "failed"
    assert failed.error_message == "prior failure reason"
