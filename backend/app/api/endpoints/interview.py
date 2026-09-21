from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    InterviewInitRequest,
    InterviewQuestionResponse,
    CandidateAnswerRequest,
    InterviewScorecardResponse
)
from app.services.interview_service import interview_service

router = APIRouter()

@router.post("/interview/start", response_model=InterviewQuestionResponse)
def start_interview(req: InterviewInitRequest):
    session_id, first_question = interview_service.create_session(req)
    return InterviewQuestionResponse(
        session_id=session_id,
        question_number=1,
        question=first_question
    )

@router.post("/interview/answer")
def submit_answer(req: CandidateAnswerRequest):
    try:
        next_q, q_num, is_complete = interview_service.process_candidate_answer(req.session_id, req.answer)
        return {
            "session_id": req.session_id,
            "question_number": q_num,
            "next_question": next_q,
            "is_complete": is_complete
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/interview/scorecard/{session_id}", response_model=InterviewScorecardResponse)
def get_scorecard(session_id: str):
    try:
        scorecard = interview_service.generate_scorecard(session_id)
        return scorecard
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
