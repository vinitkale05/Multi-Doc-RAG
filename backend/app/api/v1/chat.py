import asyncio
import json
import time
import uuid
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db, AsyncSessionLocal
from app.core.dependencies import get_current_user
from app.core.errors import AppError, NotFoundError
from app.models import User, Collection, Conversation, Message, Chunk
from app.schemas import ChatRequest, ChatResponse, CitationDetail, BibliographyItem
from app.services.retrieval.hybrid import HybridRetrievalService
from app.services.retrieval.reranker import get_reranker
from app.services.generation.prompt_builder import PromptContextBuilder
from app.services.generation.memory import ConversationMemory
from app.services.generation.providers import get_llm_provider
from app.services.citations.validator import citation_validator

router = APIRouter(tags=["Chat"])

hybrid_retriever = HybridRetrievalService()
reranker = get_reranker()
prompt_builder = PromptContextBuilder()
memory = ConversationMemory()
llm_provider = get_llm_provider()


@router.post("/chat", response_model=ChatResponse)
async def chat_query(
    req: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    start_time = time.time()
    trace_id = f"tr_{uuid.uuid4().hex[:8]}"
    current_llm = get_llm_provider()

    # 1. Validate collection access under tenant
    col_ids = req.collection_ids
    if not col_ids:
        # If no collection specified, search all user's tenant collections
        col_q = select(Collection.id).where(Collection.tenant_id == user.tenant_id)
        col_ids = (await db.execute(col_q)).scalars().all()
    else:
        col_q = select(Collection.id).where(Collection.id.in_(col_ids), Collection.tenant_id == user.tenant_id)
        valid_ids = (await db.execute(col_q)).scalars().all()
        if len(valid_ids) != len(col_ids):
            raise AppError(status_code=403, detail="Access denied to one or more requested collections")

    # 2. Get or create conversation
    conv_id = req.conversation_id
    conversation = None
    history_messages = []
    if conv_id:
        conv_q = select(Conversation).where(Conversation.id == conv_id, Conversation.user_id == user.id)
        conversation = (await db.execute(conv_q)).scalars().first()

    if not conversation:
        title = req.question[:60] if len(req.question) > 60 else req.question
        conversation = Conversation(
            user_id=user.id,
            collection_id=col_ids[0] if col_ids else None,
            title=title
        )
        db.add(conversation)
        await db.flush()
        conv_id = conversation.id
    else:
        # Load messages
        msg_q = select(Message).where(Message.conversation_id == conv_id).order_by(Message.created_at)
        history_messages = (await db.execute(msg_q)).scalars().all()

    # Save user message
    user_msg = Message(
        conversation_id=conv_id,
        role="user",
        content=req.question,
        trace_id=trace_id
    )
    db.add(user_msg)
    await db.flush()

    # 3. Hybrid Retrieval
    top_k = req.options.top_k if req.options else 30
    retrieved_candidates = await hybrid_retriever.retrieve(
        query=req.question,
        tenant_id=user.tenant_id,
        collection_ids=col_ids,
        document_ids=req.document_ids or None,
        top_k=top_k
    )

    # 4. Reranking and Abstention Check
    rerank_top_n = req.options.rerank_top_n if req.options else 8
    scored_chunks, insufficient_evidence = await reranker.rerank(
        query=req.question,
        candidates=retrieved_candidates,
        top_n=rerank_top_n
    )

    # 5. Build prompt
    system_prompt, user_prompt, source_map = prompt_builder.build_prompt(
        question=req.question,
        scored_chunks=scored_chunks
    )

    # If streaming is requested
    is_stream = req.options.stream if req.options else False
    if is_stream:
        async def event_generator():
            full_raw_tokens = []
            if insufficient_evidence or not scored_chunks:
                abstain_text = "Based on the provided documents, there is insufficient evidence to answer this question."
                for word in abstain_text.split(" "):
                    yield f"event: token\ndata: {json.dumps({'token': word + ' '})}\n\n"
                    await asyncio.sleep(0.02)

                res_payload = {
                    "answer": abstain_text,
                    "citations": [],
                    "bibliography": [],
                    "grounded": False,
                    "trace_id": trace_id,
                    "conversation_id": conv_id,
                    "message_id": str(uuid.uuid4()),
                    "latency_ms": round((time.time() - start_time) * 1000, 2)
                }
                yield f"event: result\ndata: {json.dumps(res_payload)}\n\n"
                yield "event: done\ndata: [DONE]\n\n"

                # Persist assistant message in background session
                try:
                    async with AsyncSessionLocal() as s:
                        asst_msg = Message(
                            conversation_id=conv_id,
                            role="assistant",
                            content=abstain_text,
                            citations=[],
                            bibliography=[],
                            trace_id=trace_id,
                            latency_ms=(time.time() - start_time) * 1000,
                            grounded=False
                        )
                        s.add(asst_msg)
                        await s.commit()
                except Exception as dbe:
                    print(f"Warning: could not persist abstain message: {dbe}")
                return

            # Stream tokens
            async for token in current_llm.stream_generate(system_prompt, user_prompt):
                full_raw_tokens.append(token)
                yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"

            raw_answer = "".join(full_raw_tokens)
            # Post-process citations
            validation = citation_validator.validate_and_renumber(raw_answer, source_map)
            latency = (time.time() - start_time) * 1000

            res_payload = {
                "answer": validation.cleaned_answer,
                "citations": [c.model_dump() for c in validation.citations],
                "bibliography": [b.model_dump() for b in validation.bibliography],
                "grounded": validation.grounded,
                "trace_id": trace_id,
                "conversation_id": conv_id,
                "message_id": str(uuid.uuid4()),
                "latency_ms": round(latency, 2)
            }
            yield f"event: result\ndata: {json.dumps(res_payload)}\n\n"
            yield "event: done\ndata: [DONE]\n\n"

            # Save in database
            try:
                async with AsyncSessionLocal() as s:
                    asst_msg = Message(
                        conversation_id=conv_id,
                        role="assistant",
                        content=validation.cleaned_answer,
                        citations=[c.model_dump() for c in validation.citations],
                        bibliography=[b.model_dump() for b in validation.bibliography],
                        trace_id=trace_id,
                        latency_ms=latency,
                        grounded=validation.grounded
                    )
                    s.add(asst_msg)
                    await s.commit()
            except Exception as dbe:
                print(f"Warning: could not persist assistant message: {dbe}")

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )

    # Non-streaming response
    if insufficient_evidence or not scored_chunks:
        answer_text = "Based on the provided documents, there is insufficient evidence to answer this question."
        validation = citation_validator.validate_and_renumber(answer_text, {})
    else:
        raw_answer = await current_llm.generate(system_prompt, user_prompt)
        validation = citation_validator.validate_and_renumber(raw_answer, source_map)

    latency = (time.time() - start_time) * 1000
    asst_msg = Message(
        conversation_id=conv_id,
        role="assistant",
        content=validation.cleaned_answer,
        citations=[c.model_dump() for c in validation.citations],
        bibliography=[b.model_dump() for b in validation.bibliography],
        trace_id=trace_id,
        latency_ms=latency,
        grounded=validation.grounded
    )
    db.add(asst_msg)
    await db.commit()

    return ChatResponse(
        answer=validation.cleaned_answer,
        citations=validation.citations,
        bibliography=validation.bibliography,
        grounded=validation.grounded,
        trace_id=trace_id,
        conversation_id=conv_id,
        message_id=asst_msg.id,
        latency_ms=round(latency, 2)
    )
