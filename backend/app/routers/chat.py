from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.db.session import get_db
from app.models.db_models import SessionHistory
from app.models.schemas import (
    QuestionRequest,
    AnswerResponse,
    ChatSessionRequest,
    ChatSessionResponse,
)
from app.services.retrieval_service import retrieval_service
from app.services.llm_service import llm_service
from app.services.cache_service import cache_service

router = APIRouter(prefix="/chat", tags=["Chat & Q&A"])


@router.post("", response_model=ChatSessionResponse, status_code=status.HTTP_200_OK)
@router.post("/", response_model=ChatSessionResponse, status_code=status.HTTP_200_OK)
def create_chat_session_entry(
    req: ChatSessionRequest,
    db: Session = Depends(get_db)
):
    """
    POST /api/v1/chat
    Accepts user_id, video_id, current_timestamp, and query.
    1. Checks Redis / TTL Cache for frequent query hits.
    2. Performs hybrid search (BM25 + Dense Vector Similarity) with timestamp filtering.
    3. Runs grounded RAG LLM generation with citation enforcement.
    4. Saves conversation interaction to database (SessionHistory).
    5. Returns answer along with structured source citations.
    """
    cache_key = cache_service.generate_cache_key(
        video_id=req.video_id,
        current_timestamp=req.current_timestamp,
        query=req.query,
        permitted_doc_ids=req.permitted_doc_ids,
    )

    # 1. Check Redis / In-Memory cache for frequent query hit
    cached_res = cache_service.get_cached_response(cache_key)
    if cached_res:
        # Cache Hit! Save interaction to DB and return cached response with zero LLM latency
        messages_payload = req.conversation_history.copy() if req.conversation_history else []
        messages_payload.append({"role": "user", "content": req.query, "timestamp": req.current_timestamp})
        messages_payload.append({
            "role": "assistant",
            "content": cached_res["answer"],
            "citations": cached_res["citations"],
            "is_refusal": cached_res["is_refusal"],
            "is_cached": True,
        })

        mins = int(req.current_timestamp // 60)
        secs = int(req.current_timestamp % 60)
        timestamp_range = f"00:00 - {mins:02d}:{secs:02d}"

        session_entry = SessionHistory(
            user_id=req.user_id,
            course_id=req.course_id,
            video_id=req.video_id,
            session_type="chat",
            history_data={
                "query": req.query,
                "current_timestamp": req.current_timestamp,
                "messages": messages_payload,
                "timestamp_range": timestamp_range,
                "is_cached": True,
            },
        )
        db.add(session_entry)
        db.commit()
        db.refresh(session_entry)

        return ChatSessionResponse(
            session_id=session_entry.id,
            user_id=req.user_id,
            video_id=req.video_id,
            query=req.query,
            answer=cached_res["answer"],
            citations=cached_res["citations"],
            timestamp_range_used=timestamp_range,
            is_refusal=cached_res["is_refusal"],
            refusal_reason=cached_res.get("refusal_reason"),
            latency_ms=0.0,  # Zero LLM API latency on cache hit
        )

    # 2. Cache Miss: Execute Hybrid Search (Vector + BM25) with timestamp boundary filter
    retrieved_contexts = retrieval_service.retrieve_grounded_context(
        query=req.query,
        video_id=req.video_id,
        current_timestamp=req.current_timestamp,
        permitted_doc_ids=req.permitted_doc_ids,
        top_k=5,
    )

    # 3. Run grounded RAG generation with citations and refusal handling
    answer_text, citations, is_refusal, latency_ms = llm_service.generate_grounded_answer(
        question=req.query,
        retrieved_contexts=retrieved_contexts,
        current_timestamp=req.current_timestamp,
        conversation_history=req.conversation_history,
    )

    mins = int(req.current_timestamp // 60)
    secs = int(req.current_timestamp % 60)
    timestamp_range = f"00:00 - {mins:02d}:{secs:02d}"

    # Cache generated response payload
    cache_payload = {
        "answer": answer_text,
        "citations": [c.model_dump() for c in citations],
        "is_refusal": is_refusal,
        "refusal_reason": "Information not found in watched content or permitted resources" if is_refusal else None,
    }
    cache_service.set_cached_response(cache_key, cache_payload)

    # 4. Save chat history interaction into database
    messages_payload = req.conversation_history.copy() if req.conversation_history else []
    messages_payload.append({"role": "user", "content": req.query, "timestamp": req.current_timestamp})
    messages_payload.append({
        "role": "assistant",
        "content": answer_text,
        "citations": [c.model_dump() for c in citations],
        "is_refusal": is_refusal,
        "is_cached": False,
    })

    session_entry = SessionHistory(
        user_id=req.user_id,
        course_id=req.course_id,
        video_id=req.video_id,
        session_type="chat",
        history_data={
            "query": req.query,
            "current_timestamp": req.current_timestamp,
            "messages": messages_payload,
            "timestamp_range": timestamp_range,
            "is_cached": False,
        },
    )
    db.add(session_entry)
    db.commit()
    db.refresh(session_entry)

    # 5. Return response payload
    return ChatSessionResponse(
        session_id=session_entry.id,
        user_id=req.user_id,
        video_id=req.video_id,
        query=req.query,
        answer=answer_text,
        citations=citations,
        timestamp_range_used=timestamp_range,
        is_refusal=is_refusal,
        refusal_reason=cache_payload["refusal_reason"],
        latency_ms=round(latency_ms, 2),
    )


@router.post("/ask", response_model=AnswerResponse)
def ask_question(req: QuestionRequest):
    """
    POST /chat/ask
    Direct RAG query endpoint with caching and hybrid search.
    """
    retrieved_contexts = retrieval_service.retrieve_grounded_context(
        query=req.question,
        video_id=req.video_id,
        current_timestamp=req.current_timestamp,
        permitted_doc_ids=req.allowed_resource_ids,
        top_k=5,
    )

    answer_text, citations, is_refusal, latency_ms = llm_service.generate_grounded_answer(
        question=req.question,
        retrieved_contexts=retrieved_contexts,
        current_timestamp=req.current_timestamp,
        conversation_history=req.conversation_history,
    )

    mins = int(req.current_timestamp // 60)
    secs = int(req.current_timestamp % 60)
    timestamp_range = f"00:00 - {mins:02d}:{secs:02d}"

    return AnswerResponse(
        answer=answer_text,
        citations=citations,
        timestamp_range_used=timestamp_range,
        is_refusal=is_refusal,
        refusal_reason="Information not found in watched content or permitted resources" if is_refusal else None,
        latency_ms=round(latency_ms, 2),
    )
