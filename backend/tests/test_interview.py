"""
Tests for the AI Mock Interview System
=======================================
Covers:
  - POST /api/v1/interview/start   (session init + opening question generation)
  - POST /api/v1/interview/answer  (per-turn answer processing + follow-up generation)
  - GET  /api/v1/interview/scorecard/{session_id}  (scorecard generation)
  - GET  /api/v1/interview/session/{session_id}    (transcript retrieval)
  - InterviewService unit tests (session state, question generation, error handling)
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.interview_service import (
    interview_service,
    InterviewService,
    _extract_resume_summary,
    _generate_opening_question,
    InterviewSessionState,
)
from app.models.schemas import InterviewInitRequest

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_RESUME_TEXT = """
John Smith | john@example.com | linkedin.com/in/johnsmith
Senior Software Engineer — 6 years of experience in distributed systems and cloud infrastructure.
Led design of a real-time event streaming pipeline at Acme Corp processing 200k events/second using Kafka and Flink.
Proficient in Python, Go, Kubernetes, AWS (EKS, S3, Bedrock), PostgreSQL, and Redis.
M.Sc. Computer Science, Stanford University (2019). Certified AWS Solutions Architect Professional.
"""

SAMPLE_JD = """
We are hiring a Senior ML Platform Engineer to design and scale our model serving infrastructure.
Requirements: 5+ years Python, distributed systems, Kubernetes, experience with MLOps pipelines,
familiarity with vector databases (Pinecone, Chroma), and LLM fine-tuning or RAG system design.
"""

MINIMAL_INIT_PAYLOAD = {
    "candidate_name": "Alice Chen",
    "target_role": "ML Engineer",
    "skill_level": "Intermediate",
    "interview_type": "Technical",
}

FULL_INIT_PAYLOAD = {
    "candidate_name": "John Smith",
    "target_role": "Senior ML Platform Engineer",
    "skill_level": "Senior",
    "interview_type": "Technical",
    "resume_text": SAMPLE_RESUME_TEXT,
    "job_description": SAMPLE_JD,
    "course_completed": "Fullstack AI Engineering",
    "user_id": "test_user_interview_001",
}


# ---------------------------------------------------------------------------
# TC-INT-01: POST /api/v1/interview/start — minimal payload
# ---------------------------------------------------------------------------

def test_interview_start_minimal_payload():
    """
    Test that a minimal interview init request (name + role + level + type)
    returns a valid session_id and a non-empty opening question.
    """
    response = client.post("/api/v1/interview/start", json=MINIMAL_INIT_PAYLOAD)
    assert response.status_code == 201, response.text

    data = response.json()
    assert "session_id" in data and len(data["session_id"]) > 0
    assert data["candidate_name"] == "Alice Chen"
    assert data["target_role"] == "ML Engineer"
    assert data["skill_level"] == "Intermediate"
    assert data["interview_type"] == "Technical"
    assert data["question_number"] == 1
    assert len(data["opening_question"]) > 20, "Opening question should be substantive"
    assert data["estimated_turns"] == interview_service.MAX_INTERVIEW_QUESTIONS


# ---------------------------------------------------------------------------
# TC-INT-02: POST /api/v1/interview/start — full payload with resume + JD
# ---------------------------------------------------------------------------

def test_interview_start_full_payload_with_resume_and_jd():
    """
    Test that full payload (resume_text, job_description, course_completed)
    correctly persists session state and produces an opening question.
    """
    response = client.post("/api/v1/interview/start", json=FULL_INIT_PAYLOAD)
    assert response.status_code == 201, response.text

    data = response.json()
    assert "session_id" in data
    assert data["candidate_name"] == "John Smith"
    assert data["target_role"] == "Senior ML Platform Engineer"
    assert data["skill_level"] == "Senior"

    # Resume summary should be extracted from resume_text
    assert data["resume_summary_used"] is not None
    assert len(data["resume_summary_used"]) > 0

    assert len(data["opening_question"]) > 20


# ---------------------------------------------------------------------------
# TC-INT-03: POST /api/v1/interview/start — DB persistence verified
# ---------------------------------------------------------------------------

def test_interview_start_persisted_to_db():
    """
    Test that starting an interview creates a SessionHistory record in the DB.
    """
    from app.db.session import SessionLocal
    from app.models.db_models import SessionHistory

    response = client.post("/api/v1/interview/start", json=MINIMAL_INIT_PAYLOAD)
    assert response.status_code == 201

    data = response.json()
    session_id = data["session_id"]

    # Verify in-memory session was created
    assert interview_service.session_exists(session_id)
    session = interview_service.get_session(session_id)
    assert session is not None
    assert session.db_session_id is not None

    # Verify DB record exists
    db = SessionLocal()
    try:
        db_record = db.query(SessionHistory).filter(
            SessionHistory.id == session.db_session_id
        ).first()
        assert db_record is not None
        assert db_record.session_type == "interview"
        assert db_record.history_data["candidate_name"] == "Alice Chen"
        assert db_record.history_data["question_count"] == 1
        assert len(db_record.history_data["messages"]) == 1
    finally:
        db.close()


# ---------------------------------------------------------------------------
# TC-INT-04: POST /api/v1/interview/answer — single turn
# ---------------------------------------------------------------------------

def test_interview_answer_produces_follow_up_question():
    """
    Test that submitting a candidate answer returns a follow-up question
    with incremented question_number and is_complete=False.
    """
    # Start session
    start_resp = client.post("/api/v1/interview/start", json=MINIMAL_INIT_PAYLOAD)
    assert start_resp.status_code == 201
    session_id = start_resp.json()["session_id"]

    answer_payload = {
        "session_id": session_id,
        "answer": (
            "I designed a real-time recommendation engine at my previous company. "
            "We used a hybrid retrieval approach with dense vector similarity search "
            "and BM25 re-ranking, deployed on Kubernetes with horizontal autoscaling."
        ),
    }

    response = client.post("/api/v1/interview/answer", json=answer_payload)
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["session_id"] == session_id
    assert data["question_number"] == 2
    assert len(data["question"]) > 10, "Follow-up question must be non-trivial"
    assert data["is_complete"] is False


# ---------------------------------------------------------------------------
# TC-INT-05: POST /api/v1/interview/answer — full 5-turn session to completion
# ---------------------------------------------------------------------------

def test_interview_completes_after_max_turns():
    """
    Test that after MAX_INTERVIEW_QUESTIONS answers the session is marked complete
    and the closing message is returned.
    """
    start_resp = client.post("/api/v1/interview/start", json=MINIMAL_INIT_PAYLOAD)
    assert start_resp.status_code == 201
    session_id = start_resp.json()["session_id"]

    is_complete = False
    max_turns = interview_service.MAX_INTERVIEW_QUESTIONS

    for turn in range(max_turns):
        answer_resp = client.post("/api/v1/interview/answer", json={
            "session_id": session_id,
            "answer": f"My answer to question {turn + 1}: I focused on trade-offs, scalability, and reliability.",
        })
        assert answer_resp.status_code == 200, answer_resp.text
        data = answer_resp.json()
        is_complete = data["is_complete"]

    assert is_complete is True, "Session must be marked complete after max turns"

    # Verify session state is flagged complete
    session = interview_service.get_session(session_id)
    assert session.is_complete is True


# ---------------------------------------------------------------------------
# TC-INT-06: POST /api/v1/interview/answer — invalid session_id
# ---------------------------------------------------------------------------

def test_interview_answer_invalid_session_raises_404():
    """
    Test that submitting an answer with a non-existent session_id returns 404.
    """
    response = client.post("/api/v1/interview/answer", json={
        "session_id": "non-existent-session-00000",
        "answer": "Some answer text",
    })
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# TC-INT-07: POST /api/v1/interview/answer — empty answer rejected
# ---------------------------------------------------------------------------

def test_interview_answer_empty_string_rejected():
    """
    Test that submitting an empty answer returns 422 Unprocessable Entity.
    """
    start_resp = client.post("/api/v1/interview/start", json=MINIMAL_INIT_PAYLOAD)
    assert start_resp.status_code == 201
    session_id = start_resp.json()["session_id"]

    response = client.post("/api/v1/interview/answer", json={
        "session_id": session_id,
        "answer": "   ",   # whitespace-only
    })
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# TC-INT-08: GET /api/v1/interview/scorecard/{session_id}
# ---------------------------------------------------------------------------

def test_interview_scorecard_returns_all_dimensions():
    """
    Test that the scorecard endpoint returns all required scoring dimensions
    and the scores are within the valid 0-100 range.
    """
    start_resp = client.post("/api/v1/interview/start", json=MINIMAL_INIT_PAYLOAD)
    assert start_resp.status_code == 201
    session_id = start_resp.json()["session_id"]

    # Submit a couple of answers first
    for i in range(2):
        client.post("/api/v1/interview/answer", json={
            "session_id": session_id,
            "answer": f"Answer {i+1}: detailed technical explanation of my approach.",
        })

    scorecard_resp = client.get(f"/api/v1/interview/scorecard/{session_id}")
    assert scorecard_resp.status_code == 200, scorecard_resp.text

    sc = scorecard_resp.json()
    assert sc["session_id"] == session_id
    assert 0.0 <= sc["overall_score"] <= 100.0
    assert 0.0 <= sc["technical_knowledge_score"] <= 100.0
    assert 0.0 <= sc["communication_score"] <= 100.0
    assert 0.0 <= sc["problem_solving_score"] <= 100.0
    assert 0.0 <= sc["answer_structure_score"] <= 100.0
    assert isinstance(sc["strengths"], list) and len(sc["strengths"]) > 0
    assert isinstance(sc["improvement_areas"], list) and len(sc["improvement_areas"]) > 0
    assert isinstance(sc["recommendations"], list) and len(sc["recommendations"]) > 0
    assert "estimated_operating_cost" in sc


# ---------------------------------------------------------------------------
# TC-INT-09: GET /api/v1/interview/scorecard/{session_id} — invalid session
# ---------------------------------------------------------------------------

def test_interview_scorecard_invalid_session_returns_404():
    """
    Test that requesting a scorecard for a non-existent session returns 404.
    """
    response = client.get("/api/v1/interview/scorecard/no-such-session-xyz-999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# TC-INT-10: GET /api/v1/interview/session/{session_id} — transcript retrieval
# ---------------------------------------------------------------------------

def test_interview_session_transcript_retrieval():
    """
    Test that the session transcript endpoint returns the full turn-by-turn history,
    candidate name, role, and session state metadata.
    """
    start_resp = client.post("/api/v1/interview/start", json=FULL_INIT_PAYLOAD)
    assert start_resp.status_code == 201
    session_id = start_resp.json()["session_id"]

    # Submit one answer
    client.post("/api/v1/interview/answer", json={
        "session_id": session_id,
        "answer": "I led the design of a distributed feature store for ML model serving at scale.",
    })

    transcript_resp = client.get(f"/api/v1/interview/session/{session_id}")
    assert transcript_resp.status_code == 200, transcript_resp.text

    data = transcript_resp.json()
    assert data["session_id"] == session_id
    assert data["candidate_name"] == "John Smith"
    assert data["target_role"] == "Senior ML Platform Engineer"
    assert data["skill_level"] == "Senior"
    assert data["question_count"] == 2   # 1 opening + 1 follow-up
    assert data["is_complete"] is False

    history = data["history"]
    # Should have: [interviewer opening, candidate answer, interviewer follow-up]
    assert len(history) == 3
    assert history[0]["role"] == "interviewer"
    assert history[1]["role"] == "candidate"
    assert history[2]["role"] == "interviewer"


# ---------------------------------------------------------------------------
# TC-INT-11: POST /api/v1/interview/start — validation: missing required fields
# ---------------------------------------------------------------------------

def test_interview_start_missing_required_fields_returns_422():
    """
    Test that omitting required fields (candidate_name, target_role) returns 422.
    """
    response = client.post("/api/v1/interview/start", json={
        "skill_level": "Intermediate",
        "interview_type": "Technical",
        # missing candidate_name and target_role
    })
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# TC-INT-12: InterviewService unit — resume summary extraction
# ---------------------------------------------------------------------------

def test_resume_summary_extraction():
    """
    Unit test: _extract_resume_summary should extract meaningful text lines
    from a raw resume, capped at max_chars.
    """
    summary = _extract_resume_summary(SAMPLE_RESUME_TEXT, max_chars=300)
    assert len(summary) > 0
    assert len(summary) <= 300
    # Should include at least one substantive phrase from the resume
    assert any(kw in summary for kw in ["Engineer", "Python", "Stanford", "Kafka", "AWS"])


# ---------------------------------------------------------------------------
# TC-INT-13: InterviewService unit — deterministic fallback question generation
# ---------------------------------------------------------------------------

def test_deterministic_fallback_opening_question():
    """
    Unit test: Opening question generation should return a non-empty string
    even without an LLM API key configured (uses deterministic templates).
    """
    svc = InterviewService()
    session = InterviewSessionState(
        session_id="test-unit-session-001",
        db_session_id=None,
        candidate_name="Test Candidate",
        target_role="Data Engineer",
        skill_level="Entry",
        interview_type="System Design",
        resume_text=None,
        resume_summary=None,
        job_description=None,
        course_completed=None,
        user_id=None,
    )
    question = _generate_opening_question(session)
    assert isinstance(question, str)
    assert len(question) > 20


# ---------------------------------------------------------------------------
# TC-INT-14: InterviewService unit — session state isolation
# ---------------------------------------------------------------------------

def test_interview_session_state_isolation():
    """
    Unit test: Two concurrent sessions should be completely independent —
    answers to one must not affect the other.
    """
    req_a = InterviewInitRequest(
        candidate_name="Candidate A",
        target_role="Backend Engineer",
        skill_level="Intermediate",
        interview_type="Technical",
    )
    req_b = InterviewInitRequest(
        candidate_name="Candidate B",
        target_role="Data Scientist",
        skill_level="Entry",
        interview_type="Behavioral",
    )

    svc = InterviewService()
    state_a, _ = svc.create_session(req_a)
    state_b, _ = svc.create_session(req_b)

    assert state_a.session_id != state_b.session_id
    assert state_a.candidate_name == "Candidate A"
    assert state_b.candidate_name == "Candidate B"

    # Answer session A — session B must remain untouched
    svc.process_answer(state_a.session_id, "Answer from candidate A.")
    session_a = svc.get_session(state_a.session_id)
    session_b = svc.get_session(state_b.session_id)

    assert session_a.question_count == 2   # 1 opening + 1 answer turn
    assert session_b.question_count == 1   # still only opening question
