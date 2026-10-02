"""
Interview Router — AI Mock Interview Session Endpoints
======================================================
Endpoints:
  POST /api/v1/interview/start    — Initialize session, return tailored opening question
  POST /api/v1/interview/answer   — Submit candidate answer, receive next question
  GET  /api/v1/interview/scorecard/{session_id} — Retrieve evaluation scorecard
  GET  /api/v1/interview/session/{session_id}   — Retrieve full session transcript
"""
import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.models.db_models import SessionHistory
from app.models.schemas import (
    InterviewInitRequest,
    InterviewStartResponse,
    InterviewQuestionResponse,
    CandidateAnswerRequest,
    InterviewScorecardResponse,
)
from app.services.interview_service import interview_service, InterviewSessionState

router = APIRouter(prefix="/interview", tags=["Mock Interview"])


# ---------------------------------------------------------------------------
# POST /api/v1/interview/start
# ---------------------------------------------------------------------------

@router.post(
    "/start",
    response_model=InterviewStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new AI mock interview session",
    description=(
        "Accepts candidate resume text, target job description, role, and skill level. "
        "Creates a persistent interview session and returns the AI-generated opening question "
        "tailored to the candidate's background."
    ),
)
def start_interview(
    req: InterviewInitRequest,
    db: Session = Depends(get_db),
) -> InterviewStartResponse:
    """
    POST /api/v1/interview/start

    1. Extracts resume summary from full resume text (if provided).
    2. Creates in-memory interview session with candidate context.
    3. Generates an LLM-tailored opening question based on role, JD, skill level, and resume.
    4. Persists initial session state to SessionHistory DB table.
    5. Returns session_id + opening_question for the client to begin the interview loop.
    """
    start_ts = time.perf_counter()

    # Create session and generate opening question
    session, opening_question = interview_service.create_session(req)

    # Persist initial session state to database
    history_data = session.to_history_data()
    history_data["latency_ms"] = round((time.perf_counter() - start_ts) * 1000, 2)

    db_record = SessionHistory(
        user_id=req.user_id or "anonymous",
        course_id=None,
        video_id=None,
        session_type="interview",
        history_data=history_data,
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    # Link DB record ID back into the in-memory session for subsequent persistence
    session.db_session_id = db_record.id

    return InterviewStartResponse(
        session_id=session.session_id,
        candidate_name=session.candidate_name,
        target_role=session.target_role,
        skill_level=session.skill_level,
        interview_type=session.interview_type,
        question_number=1,
        opening_question=opening_question,
        resume_summary_used=session.resume_summary,
        estimated_turns=interview_service.MAX_INTERVIEW_QUESTIONS,
    )


# ---------------------------------------------------------------------------
# POST /api/v1/interview/answer
# ---------------------------------------------------------------------------

@router.post(
    "/answer",
    response_model=InterviewQuestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit candidate answer and receive next adaptive interview question",
    description=(
        "Submit the candidate's answer to the current question. "
        "The AI interviewer analyzes the answer and generates the next contextually relevant question, "
        "escalating in depth based on the response quality."
    ),
)
def submit_answer(
    req: CandidateAnswerRequest,
    db: Session = Depends(get_db),
) -> InterviewQuestionResponse:
    """
    POST /api/v1/interview/answer

    1. Validates the session exists and is still active.
    2. Records the candidate's answer in session history.
    3. Generates the next adaptive follow-up question using LLM (or fallback templates).
    4. Updates the persisted SessionHistory DB record.
    5. Returns next question or interview completion signal.
    """
    if not interview_service.session_exists(req.session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview session '{req.session_id}' not found. Sessions expire after server restart.",
        )

    if not req.answer or not req.answer.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Answer text cannot be empty.",
        )

    try:
        next_question, question_num, is_complete = interview_service.process_answer(
            session_id=req.session_id,
            answer=req.answer.strip(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # Update DB record with latest session state
    session = interview_service.get_session(req.session_id)
    if session and session.db_session_id:
        try:
            db_record = db.query(SessionHistory).filter(
                SessionHistory.id == session.db_session_id
            ).first()
            if db_record:
                db_record.history_data = session.to_history_data()
                db.commit()
        except Exception:
            db.rollback()

    return InterviewQuestionResponse(
        session_id=req.session_id,
        question_number=question_num,
        question=next_question,
        is_complete=is_complete,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/interview/scorecard/{session_id}
# ---------------------------------------------------------------------------

@router.get(
    "/scorecard/{session_id}",
    response_model=InterviewScorecardResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve the AI-evaluated scorecard for a completed interview session",
    description=(
        "Evaluates the full interview transcript using the LLM to score the candidate across "
        "technical knowledge, communication, problem-solving, and answer structure dimensions."
    ),
)
def get_scorecard(
    session_id: str,
    db: Session = Depends(get_db),
) -> InterviewScorecardResponse:
    """
    GET /api/v1/interview/scorecard/{session_id}

    1. Retrieves the session transcript.
    2. Sends transcript to LLM for structured evaluation.
    3. Persists scorecard JSON to SessionHistory.scorecard column.
    4. Returns scored dimensions, strengths, improvement areas, and recommendations.
    """
    if not interview_service.session_exists(session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview session '{session_id}' not found.",
        )

    try:
        scorecard = interview_service.generate_scorecard(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # Persist scorecard to DB
    session = interview_service.get_session(session_id)
    if session and session.db_session_id:
        try:
            db_record = db.query(SessionHistory).filter(
                SessionHistory.id == session.db_session_id
            ).first()
            if db_record:
                db_record.scorecard = scorecard.model_dump()
                db.commit()
        except Exception:
            db.rollback()

    return scorecard


# ---------------------------------------------------------------------------
# GET /api/v1/interview/session/{session_id}
# ---------------------------------------------------------------------------

@router.get(
    "/session/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Retrieve full session transcript and metadata",
    description="Returns the complete turn-by-turn interview transcript and session metadata.",
)
def get_session_transcript(
    session_id: str,
) -> dict:
    """
    GET /api/v1/interview/session/{session_id}

    Returns full session state: metadata, transcript history, and completion status.
    Useful for frontend display of the interview playback.
    """
    if not interview_service.session_exists(session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview session '{session_id}' not found.",
        )

    session = interview_service.get_session(session_id)
    return {
        "session_id": session_id,
        "candidate_name": session.candidate_name,
        "target_role": session.target_role,
        "skill_level": session.skill_level,
        "interview_type": session.interview_type,
        "question_count": session.question_count,
        "is_complete": session.is_complete,
        "resume_summary": session.resume_summary,
        "history": session.history,
        "estimated_turns": interview_service.MAX_INTERVIEW_QUESTIONS,
    }
