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
    1. Calls timestamp filter & vector search for grounded contexts.
    2. Runs grounded RAG LLM generation with citation enforcement.
    3. Saves conversation interaction to database (SessionHistory).
    4. Returns generated answer along with structured source citations.
    """
    # 1. Execute vector search with timestamp boundary filter
    retrieved_contexts = retrieval_service.retrieve_grounded_context(
        query=req.query,
        video_id=req.video_id,
        current_timestamp=req.current_timestamp,
        permitted_doc_ids=req.permitted_doc_ids,
        top_k=5,
    )

    # 2. Run grounded RAG generation with citations and refusal handling
    answer_text, citations, is_refusal, latency_ms = llm_service.generate_grounded_answer(
        question=req.query,
        retrieved_contexts=retrieved_contexts,
        current_timestamp=req.current_timestamp,
        conversation_history=req.conversation_history,
    )

    # Format timestamp range
    mins = int(req.current_timestamp // 60)
    secs = int(req.current_timestamp % 60)
    timestamp_range = f"00:00 - {mins:02d}:{secs:02d}"

    # 3. Save chat history interaction into database
    messages_payload = []
    if req.conversation_history:
        messages_payload.extend(req.conversation_history)

    messages_payload.append({"role": "user", "content": req.query, "timestamp": req.current_timestamp})
    messages_payload.append({
        "role": "assistant",
        "content": answer_text,
        "citations": [c.model_dump() for c in citations],
        "is_refusal": is_refusal,
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
        },
    )
    db.add(session_entry)
    db.commit()
    db.refresh(session_entry)

    # 4. Return answer response payload with DB session_id
    return ChatSessionResponse(
        session_id=session_entry.id,
        user_id=req.user_id,
        video_id=req.video_id,
        query=req.query,
        answer=answer_text,
        citations=citations,
        timestamp_range_used=timestamp_range,
        is_refusal=is_refusal,
        refusal_reason="Information not found in watched content or permitted resources" if is_refusal else None,
        latency_ms=round(latency_ms, 2),
    )


@router.post("/ask", response_model=AnswerResponse)
def ask_question(req: QuestionRequest):
    """
    POST /chat/ask
    Direct RAG query endpoint without database persistence requirement.
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
