from fastapi import APIRouter, HTTPException
from app.models.schemas import QuestionRequest, AnswerResponse, QuizGenerateRequest, QuizResponse, QuizQuestion
from app.services.retrieval_service import retrieval_service
from app.services.llm_service import llm_service

router = APIRouter()

@router.post("/ask", response_model=AnswerResponse)
def ask_question(req: QuestionRequest):
    contexts = retrieval_service.retrieve_context(
        query=req.question,
        video_id=req.video_id,
        current_timestamp=req.current_timestamp,
        allowed_resources=req.allowed_resource_ids
    )
    
    answer_text, citations, is_refusal, latency_ms = llm_service.generate_grounded_answer(
        question=req.question,
        retrieved_contexts=contexts,
        current_timestamp=req.current_timestamp
    )
    
    mins = int(req.current_timestamp // 60)
    secs = int(req.current_timestamp % 60)
    timestamp_range = f"00:00 - {mins:02d}:{secs:02d}"
    
    return AnswerResponse(
        answer=answer_text,
        citations=citations,
        timestamp_range_used=timestamp_range,
        is_refusal=is_refusal,
        latency_ms=latency_ms
    )

@router.post("/quiz", response_model=QuizResponse)
def generate_quiz(req: QuizGenerateRequest):
    # Retrieve content watched so far up to current timestamp
    contexts = retrieval_service.retrieve_context(
        query="core concepts principles key takeaways",
        video_id=req.video_id,
        current_timestamp=req.current_timestamp,
        top_k=req.num_questions
    )
    
    questions = []
    for idx, ctx in enumerate(contexts[:req.num_questions]):
        questions.append(
            QuizQuestion(
                id=f"q_{idx+1}",
                question=f"Based on topic discussed around timestamp {int(ctx.get('start_time', 0))}s: What is the primary focus of this section?",
                options=[
                    ctx['content'][:60] + "...",
                    "Unrelated future topic not covered yet",
                    "Alternative implementation detail",
                    "None of the above"
                ],
                correct_option_index=0,
                explanation=f"This was covered in the lecture transcript: '{ctx['content'][:100]}...'"
            )
        )
        
    return QuizResponse(
        video_id=req.video_id,
        current_timestamp=req.current_timestamp,
        questions=questions
    )
