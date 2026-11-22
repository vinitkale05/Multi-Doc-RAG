from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.errors import NotFoundError
from app.models import User, Message, Feedback
from app.schemas import FeedbackCreate, FeedbackResponse

router = APIRouter(prefix="/messages", tags=["Feedback"])


@router.post("/{message_id}/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    message_id: str,
    req: FeedbackCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    msg_q = select(Message).where(Message.id == message_id)
    msg = (await db.execute(msg_q)).scalars().first()
    if not msg:
        raise NotFoundError("Message", message_id)

    # Check if feedback exists
    fb_q = select(Feedback).where(Feedback.message_id == message_id)
    feedback = (await db.execute(fb_q)).scalars().first()
    if feedback:
        feedback.rating = req.rating
        feedback.reason = req.reason
    else:
        feedback = Feedback(
            message_id=message_id,
            rating=req.rating,
            reason=req.reason
        )
        db.add(feedback)

    await db.commit()
    return FeedbackResponse(
        id=feedback.id,
        message_id=feedback.message_id,
        rating=feedback.rating,
        reason=feedback.reason,
        created_at=feedback.created_at
    )
