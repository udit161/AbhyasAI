"""
Tests for Post-Interview Scorecard & Feedback Generator (Task 5.3)
===================================================================
Covers:
  - GET /api/v1/interview/scorecard/{session_id}
  - POST /api/v1/interview/scorecard
  - 4 scoring metrics + overall score + strengths + improvement areas + recommendations
  - Estimated operating cost calculation format
  - Auto-triggering evaluation when session reaches completion
  - Score scaling based on transcript answer quality
  - DB persistence of scorecard JSON
  - Invalid session error handling
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import get_db
from app.models.db_models import Base, SessionHistory
from app.services.interview_service import interview_service

# Setup in-memory SQLite DB for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_environment():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    interview_service._sessions.clear()
    yield
    interview_service._sessions.clear()
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


MINIMAL_INIT_PAYLOAD = {
    "candidate_name": "Scorecard Tester",
    "target_role": "Backend Engineer",
    "skill_level": "Intermediate",
    "interview_type": "Technical",
}

FULL_INIT_PAYLOAD = {
    "candidate_name": "Senior Architect",
    "target_role": "System Architect",
    "skill_level": "Senior",
    "interview_type": "System Design",
    "job_description": "Architect scalable distributed systems with Redis, Kafka, PostgreSQL sharding, and SLO monitoring.",
    "resume_text": "Experienced architect with 8 years leading microservice design and high-throughput pipelines.",
}


# ---------------------------------------------------------------------------
# 1. GET & POST Scorecard Endpoints
# ---------------------------------------------------------------------------

def test_get_and_post_scorecard_endpoints():
    """Verifies both GET /scorecard/{id} and POST /scorecard return 200 OK with identical valid schema."""
    start_resp = client.post("/api/v1/interview/start", json=MINIMAL_INIT_PAYLOAD)
    assert start_resp.status_code == 201
    session_id = start_resp.json()["session_id"]

    # Submit an answer
    client.post("/api/v1/interview/answer", json={
        "session_id": session_id,
        "answer": "I used Redis caching and read replicas to optimize database queries under heavy load.",
    })

    # GET endpoint
    get_resp = client.get(f"/api/v1/interview/scorecard/{session_id}")
    assert get_resp.status_code == 200, get_resp.text
    get_data = get_resp.json()

    # POST endpoint
    post_resp = client.post("/api/v1/interview/scorecard", json={"session_id": session_id})
    assert post_resp.status_code == 200, post_resp.text
    post_data = post_resp.json()

    assert get_data["session_id"] == session_id
    assert post_data["session_id"] == session_id
    assert get_data["overall_score"] == post_data["overall_score"]


# ---------------------------------------------------------------------------
# 2. Scorecard Metrics & Dimensions
# ---------------------------------------------------------------------------

def test_scorecard_metrics_range_and_structure():
    """Verifies all required scoring dimensions exist, are within 0-100, and feedback lists are populated."""
    start_resp = client.post("/api/v1/interview/start", json=MINIMAL_INIT_PAYLOAD)
    session_id = start_resp.json()["session_id"]

    client.post("/api/v1/interview/answer", json={
        "session_id": session_id,
        "answer": "We applied rate limiting and token bucket algorithms to handle spike traffic.",
    })

    resp = client.get(f"/api/v1/interview/scorecard/{session_id}")
    assert resp.status_code == 200
    sc = resp.json()

    # Scores within 0-100 range
    assert 0.0 <= sc["overall_score"] <= 100.0
    assert 0.0 <= sc["technical_knowledge_score"] <= 100.0
    assert 0.0 <= sc["communication_score"] <= 100.0
    assert 0.0 <= sc["problem_solving_score"] <= 100.0
    assert 0.0 <= sc["answer_structure_score"] <= 100.0

    # Lists populated
    assert isinstance(sc["strengths"], list) and len(sc["strengths"]) >= 1
    assert isinstance(sc["improvement_areas"], list) and len(sc["improvement_areas"]) >= 1
    assert isinstance(sc["recommendations"], list) and len(sc["recommendations"]) >= 1


# ---------------------------------------------------------------------------
# 3. Estimated Operating Cost Format
# ---------------------------------------------------------------------------

def test_scorecard_operating_cost_format():
    """Verifies estimated_operating_cost contains USD currency symbol, turn count, and token info."""
    start_resp = client.post("/api/v1/interview/start", json=MINIMAL_INIT_PAYLOAD)
    session_id = start_resp.json()["session_id"]

    client.post("/api/v1/interview/answer", json={
        "session_id": session_id,
        "answer": "Detailed answer covering architecture, latency bounds, and fallback strategies.",
    })

    resp = client.get(f"/api/v1/interview/scorecard/{session_id}")
    assert resp.status_code == 200
    cost_str = resp.json()["estimated_operating_cost"]

    assert "$" in cost_str
    assert "USD" in cost_str
    assert "turn" in cost_str
    assert "tokens" in cost_str


# ---------------------------------------------------------------------------
# 4. Auto-Trigger Scorecard on Completion
# ---------------------------------------------------------------------------

def test_scorecard_auto_triggered_on_interview_completion():
    """Verifies that reaching maximum turns pre-populates session.scorecard automatically."""
    start_resp = client.post("/api/v1/interview/start", json=MINIMAL_INIT_PAYLOAD)
    session_id = start_resp.json()["session_id"]

    max_turns = interview_service.MAX_INTERVIEW_QUESTIONS
    for i in range(max_turns):
        resp = client.post("/api/v1/interview/answer", json={
            "session_id": session_id,
            "answer": f"Turn {i+1} response with trade-off analysis and metric monitoring.",
        })

    assert resp.json()["is_complete"] is True

    session = interview_service.get_session(session_id)
    assert session is not None
    assert session.is_complete is True
    assert session.scorecard is not None
    assert session.scorecard.session_id == session_id


# ---------------------------------------------------------------------------
# 5. Score Scaling Based on Transcript Quality
# ---------------------------------------------------------------------------

def test_scorecard_evaluates_transcript_depth():
    """Verifies that a transcript with technical depth scores higher than minimal answers."""
    # Session A: minimal answers
    start_a = client.post("/api/v1/interview/start", json=MINIMAL_INIT_PAYLOAD).json()
    id_a = start_a["session_id"]
    client.post("/api/v1/interview/answer", json={"session_id": id_a, "answer": "yes, i did that"})
    sc_a = client.get(f"/api/v1/interview/scorecard/{id_a}").json()

    # Session B: deep technical answers with architecture, trade-offs, metrics
    start_b = client.post("/api/v1/interview/start", json=FULL_INIT_PAYLOAD).json()
    id_b = start_b["session_id"]
    client.post("/api/v1/interview/answer", json={
        "session_id": id_b,
        "answer": (
            "First, I designed the distributed event streaming pipeline using Kafka for message queuing "
            "with a 3-replica topic partition strategy. We mitigated failure modes by implementing a retry "
            "dead-letter queue and circuit breaker pattern. Latency dropped from 250ms to 18ms at scale, "
            "and we maintained strict SLOs of 99.99% availability."
        )
    })
    sc_b = client.get(f"/api/v1/interview/scorecard/{id_b}").json()

    # Compare technical & problem solving scores
    assert sc_b["technical_knowledge_score"] > sc_a["technical_knowledge_score"]
    assert sc_b["problem_solving_score"] > sc_a["problem_solving_score"]
    assert sc_b["overall_score"] > sc_a["overall_score"]


# ---------------------------------------------------------------------------
# 6. DB Persistence of Scorecard
# ---------------------------------------------------------------------------

def test_scorecard_persisted_to_database():
    """Verifies that calling /scorecard saves the scorecard JSON into SessionHistory.scorecard column in DB."""
    start_resp = client.post("/api/v1/interview/start", json=MINIMAL_INIT_PAYLOAD)
    session_id = start_resp.json()["session_id"]

    client.post("/api/v1/interview/answer", json={
        "session_id": session_id,
        "answer": "I implemented caching and database index optimizations.",
    })

    # Fetch scorecard to trigger DB persistence
    scorecard_resp = client.get(f"/api/v1/interview/scorecard/{session_id}")
    assert scorecard_resp.status_code == 200

    db = TestingSessionLocal()
    session = interview_service.get_session(session_id)
    db_record = db.query(SessionHistory).filter(SessionHistory.id == session.db_session_id).first()
    assert db_record is not None
    assert db_record.scorecard is not None
    assert db_record.scorecard["session_id"] == session_id
    db.close()


# ---------------------------------------------------------------------------
# 7. Invalid Session Error Handling
# ---------------------------------------------------------------------------

def test_scorecard_invalid_session_returns_404():
    """Verifies requesting scorecard for non-existent session returns 404 Not Found."""
    get_resp = client.get("/api/v1/interview/scorecard/non-existent-session-12345")
    assert get_resp.status_code == 404

    post_resp = client.post("/api/v1/interview/scorecard", json={"session_id": "non-existent-session-12345"})
    assert post_resp.status_code == 404
