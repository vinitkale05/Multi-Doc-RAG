from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.errors import NotFoundError
from app.models import User, Conversation, Message
from app.schemas import ConversationResponse, MessageResponse

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.get("", response_model=List[ConversationResponse])
async def list_conversations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.created_at.desc())
    conversations = (await db.execute(query)).scalars().all()
    return conversations


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    q = select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id)
    conv = (await db.execute(q)).scalars().first()
    if not conv:
        raise NotFoundError("Conversation", conversation_id)

    msg_q = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
    messages = (await db.execute(msg_q)).scalars().all()

    return ConversationResponse(
        id=conv.id,
        user_id=conv.user_id,
        collection_id=conv.collection_id,
        title=conv.title,
        created_at=conv.created_at,
        messages=[
            MessageResponse(
                id=m.id,
                conversation_id=m.conversation_id,
                role=m.role,
                content=m.content,
                citations=m.citations or [],
                bibliography=m.bibliography or [],
                trace_id=m.trace_id,
                grounded=m.grounded,
                created_at=m.created_at
            )
            for m in messages
        ]
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    q = select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id)
    conv = (await db.execute(q)).scalars().first()
    if not conv:
        raise NotFoundError("Conversation", conversation_id)
    await db.delete(conv)
    await db.commit()
    return None
