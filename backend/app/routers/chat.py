import json
import logging
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sse_starlette.sse import EventSourceResponse

from app.database import get_db
from app.dependencies import CurrentUser
from app.exceptions import NotFoundError, ValidationError
from app.models.conversation import Conversation, Message
from app.services.rag import (
    build_context,
    get_filename_map,
    retrieve_chunks,
    stream_rag_response,
)
from app.services.rate_limiter import chat_rate_limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


class ChatRequest(BaseModel):
    message: str
    document_ids: list[str]
    conversation_id: str | None = None


@router.post("/chat")
async def chat(request: ChatRequest, db: DbSession, current_user: CurrentUser):
    if not request.document_ids:
        raise ValidationError(
            "Select at least one document to chat.",
            code="NO_DOCUMENTS",
        )

    # Rate limit check
    chat_rate_limiter.check(current_user.id)

    # Get or create conversation
    conversation: Conversation
    if request.conversation_id:
        result = await db.execute(
            select(Conversation)
            .where(
                Conversation.id == request.conversation_id,
                Conversation.user_id == current_user.id,
            )
            .options(selectinload(Conversation.messages))
        )
        conv = result.scalar_one_or_none()
        if not conv:
            raise NotFoundError("Conversation not found")
        conversation = conv
    else:
        # Create new conversation with first ~50 chars of message as title
        title = request.message[:50].strip()
        if len(request.message) > 50:
            title += "..."
        conversation = Conversation(title=title, user_id=current_user.id)
        db.add(conversation)
        await db.flush()

    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.message,
    )
    db.add(user_message)
    await db.flush()

    # Retrieve relevant chunks
    search_results = await retrieve_chunks(
        db=db,
        query=request.message,
        document_ids=request.document_ids,
    )

    # Get filename map for citation display
    filename_map = await get_filename_map(request.document_ids, db)

    # Build source chunks for storage
    _context, source_chunks = build_context(search_results, filename_map)
    source_chunks_json = json.dumps([
        {
            "chunk_id": sc.chunk_id,
            "document_id": sc.document_id,
            "filename": sc.filename,
            "page_number": sc.page_number,
            "score": sc.score,
        }
        for sc in source_chunks
    ])

    # Build conversation history for context
    conversation_history: list[dict[str, str]] = []
    if request.conversation_id and conversation.messages:
        for msg in conversation.messages:
            if msg.id != user_message.id:
                conversation_history.append({"role": msg.role, "content": msg.content})

    # Commit before streaming so conversation/user message are persisted
    await db.commit()

    async def event_generator() -> AsyncGenerator[dict, None]:
        full_response = ""
        try:
            # Send conversation_id first so the frontend knows it
            yield {
                "event": "metadata",
                "data": json.dumps({
                    "conversation_id": conversation.id,
                    "source_chunks": json.loads(source_chunks_json),
                }),
            }

            for token in stream_rag_response(
                query=request.message,
                search_results=search_results,
                filename_map=filename_map,
                conversation_history=conversation_history,
            ):
                full_response += token
                yield {"event": "token", "data": token}

            yield {"event": "done", "data": ""}
        except Exception as e:
            logger.exception("Streaming error")
            yield {"event": "error", "data": str(e)}
            return

        # Save assistant message after streaming completes
        try:
            async with db.begin():
                assistant_message = Message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=full_response,
                    source_chunks=source_chunks_json,
                )
                db.add(assistant_message)
        except Exception:
            logger.exception("Failed to save assistant message")

    return EventSourceResponse(event_generator())
