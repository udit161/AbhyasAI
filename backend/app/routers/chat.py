from fastapi import APIRouter
from app.models.schemas import QuestionRequest, AnswerResponse
from app.services.retrieval_service import retrieval_service
from app.services.llm_service import llm_service

router = APIRouter(prefix="/chat", tags=["Chat & Q&A"])


@router.post("/ask", response_model=AnswerResponse)
def ask_question(req: QuestionRequest):
    """
    POST /chat/ask
    Receives video_id, current_timestamp, question, conversation_history, and allowed_resource_ids.
    Retrieves grounded context with timestamp filtering and generates an answer with strict citations.
    """
    # 1. Retrieve grounded context strictly bounded to current_timestamp
    retrieved_contexts = retrieval_service.retrieve_grounded_context(
        query=req.question,
        video_id=req.video_id,
        current_timestamp=req.current_timestamp,
        permitted_doc_ids=req.allowed_resource_ids,
        top_k=5,
    )

    # 2. Generate grounded answer with explicit citations and refusal handling
    answer_text, citations, is_refusal, latency_ms = llm_service.generate_grounded_answer(
        question=req.question,
        retrieved_contexts=retrieved_contexts,
        current_timestamp=req.current_timestamp,
        conversation_history=req.conversation_history,
    )

    # Format playback position timestamp range string
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
