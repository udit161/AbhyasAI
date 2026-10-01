from fastapi import APIRouter
from app.schemas import ChatAskRequest, ChatAskResponse

router = APIRouter(prefix="/chat", tags=["Chat & Q&A"])

@router.post("/ask", response_model=ChatAskResponse)
def ask_chat_question(req: ChatAskRequest):
    """
    POST /chat/ask
    Receives course_id, video_id, current_timestamp, and question.
    Validates request body with Pydantic.
    Returns a clearly labeled mock response without calling an AI model.
    """
    mock_answer = (
        f"[MOCK ANSWER] Thank you for asking: '{req.question}'. "
        f"This response is simulated for Course '{req.course_id}', "
        f"Video '{req.video_id}' at timestamp {req.current_timestamp:.1f}s."
    )
    
    return ChatAskResponse(
        status="success",
        is_mock=True,
        message="[MOCK RESPONSE] AI LLM integration is disabled in Phase 1.",
        course_id=req.course_id,
        video_id=req.video_id,
        current_timestamp=req.current_timestamp,
        question=req.question,
        mock_answer=mock_answer
    )
