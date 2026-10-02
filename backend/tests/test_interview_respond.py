"""
Tests for POST /api/v1/interview/respond — Dynamic PROBE/TRANSITION Agent
=========================================================================
Covers:
  - PROBE decision triggered on short/shallow answers
  - TRANSITION decision triggered on thorough answers
  - Topic tracking state (covered_topics, remaining_topics, probe_counts)
  - Max probe ceiling forcing transition after 2 probes on same topic
  - DB persistence of agent decision log
  - All required fields present in InterviewRespondResponse
  - Error cases: invalid session, empty answer
  - JD competency extraction unit tests
  - Deterministic fallback agent decision tests
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.interview_service import (
    interview_service,
    InterviewService,
    InterviewSessionState,
    _extract_jd_competencies,
    _deterministic_agent_decision,
    _run_agent_decision,
    _parse_llm_json,
    _MAX_PROBES_PER_TOPIC,
)
from app.models.schemas import InterviewInitRequest

client = TestClient(app)


# ---------------------------------------------------------------------------
# Shared test fixtures
# ---------------------------------------------------------------------------

FULL_JD = """
We are hiring a Senior ML Platform Engineer.
Requirements: Python, Kubernetes, distributed systems, Kafka, Redis caching,
vector databases (Pinecone, Chroma), RAG systems and LLM integration,
CI/CD automation, observability with Prometheus and Grafana.
"""

BASE_INIT = {
    "candidate_name": "Priya Sharma",
    "target_role": "Senior ML Platform Engineer",
    "skill_level": "Senior",
    "interview_type": "Technical",
    "job_description": FULL_JD,
}

SHORT_ANSWER = "I used Redis for caching."

THOROUGH_ANSWER = (
    "We faced a significant scaling challenge: the existing Redis cluster was handling ~50k ops/sec "
    "but latency spiked during peak because all cache keys were on the same shard. "
    "I implemented consistent hashing with virtual nodes, splitting across 8 shards. "
    "The trade-off was increased memory overhead (~15%) for the routing table, but latency "
    "dropped from 180ms p99 to 22ms. We monitored this with Prometheus + Grafana and had "
    "automated rollback via Helm if error rate exceeded 0.1% over 5 minutes."
)


def _start_session(payload: dict = None) -> str:
    """Helper: start a session and return session_id."""
    resp = client.post("/api/v1/interview/start", json=payload or BASE_INIT)
    assert resp.status_code == 201, resp.text
    return resp.json()["session_id"]


# ---------------------------------------------------------------------------
# TC-RESP-01: Response schema completeness
# ---------------------------------------------------------------------------

def test_respond_returns_all_required_fields():
    """
    Test that /respond always returns all required fields in InterviewRespondResponse.
    """
    sid = _start_session()
    resp = client.post("/api/v1/interview/respond", json={
        "session_id": sid,
        "answer": SHORT_ANSWER,
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()

    required_fields = [
        "session_id", "question_number", "question", "decision",
        "reasoning", "answer_quality", "topics_covered_so_far",
        "topics_remaining", "is_complete", "latency_ms",
    ]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"

    assert data["session_id"] == sid
    assert data["question_number"] >= 2
    assert len(data["question"]) > 10
    assert data["decision"] in ("probe", "transition", "complete")
    assert data["answer_quality"] in ("strong", "adequate", "weak", "incomplete", "n/a")
    assert isinstance(data["topics_remaining"], list)
    assert isinstance(data["topics_covered_so_far"], list)
    assert data["is_complete"] is False
    assert data["latency_ms"] >= 0.0


# ---------------------------------------------------------------------------
# TC-RESP-02: Short answer triggers PROBE
# ---------------------------------------------------------------------------

def test_short_answer_triggers_probe_decision():
    """
    A very short, shallow answer should cause the deterministic agent to decide PROBE.
    (No LLM key in test env → deterministic fallback is always used.)
    """
    sid = _start_session()
    resp = client.post("/api/v1/interview/respond", json={
        "session_id": sid,
        "answer": "I used Kafka for streaming.",   # short, no trade-offs
    })
    assert resp.status_code == 200
    data = resp.json()

    assert data["decision"] == "probe", (
        f"Expected 'probe' for short answer, got '{data['decision']}'. "
        f"Reasoning: {data['reasoning']}"
    )
    assert data["answer_quality"] in ("weak", "incomplete")
    assert data["probe_target"] is not None
    assert data["next_topic"] is None   # probe stays on same topic


# ---------------------------------------------------------------------------
# TC-RESP-03: Thorough answer triggers TRANSITION
# ---------------------------------------------------------------------------

def test_thorough_answer_triggers_transition():
    """
    A detailed, metrics-rich answer with trade-off reasoning should cause TRANSITION
    to a new JD competency.
    """
    sid = _start_session()
    resp = client.post("/api/v1/interview/respond", json={
        "session_id": sid,
        "answer": THOROUGH_ANSWER,
    })
    assert resp.status_code == 200
    data = resp.json()

    assert data["decision"] == "transition", (
        f"Expected 'transition' for thorough answer, got '{data['decision']}'. "
        f"Reasoning: {data['reasoning']}"
    )
    assert data["answer_quality"] in ("strong", "adequate")
    assert data["next_topic"] is not None
    assert data["topic_covered"] is not None


# ---------------------------------------------------------------------------
# TC-RESP-04: Max probes ceiling forces transition
# ---------------------------------------------------------------------------

def test_max_probe_ceiling_forces_transition():
    """
    After MAX_PROBES_PER_TOPIC probe decisions on the same topic,
    the next call must TRANSITION regardless of answer quality.
    """
    sid = _start_session()

    # Force MAX_PROBES_PER_TOPIC probe turns with short answers
    for _ in range(_MAX_PROBES_PER_TOPIC):
        r = client.post("/api/v1/interview/respond", json={
            "session_id": sid,
            "answer": "I'm not sure about the exact details.",
        })
        assert r.status_code == 200

    # Now the probe count ceiling is hit — next must be transition
    r = client.post("/api/v1/interview/respond", json={
        "session_id": sid,
        "answer": "I still don't have much detail on that.",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["decision"] == "transition", (
        f"Expected forced transition after {_MAX_PROBES_PER_TOPIC} probes, "
        f"got '{data['decision']}'"
    )


# ---------------------------------------------------------------------------
# TC-RESP-05: Topic tracking accumulates correctly
# ---------------------------------------------------------------------------

def test_topic_coverage_tracking_accumulates():
    """
    After a TRANSITION decision, the topic should appear in topics_covered_so_far
    on the next call.
    """
    sid = _start_session()

    # First call: thorough answer → TRANSITION
    r1 = client.post("/api/v1/interview/respond", json={
        "session_id": sid, "answer": THOROUGH_ANSWER,
    })
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["decision"] == "transition"
    topic_that_was_covered = d1.get("topic_covered")

    # Second call: check topics_covered_so_far contains the transitioned topic
    r2 = client.post("/api/v1/interview/respond", json={
        "session_id": sid, "answer": SHORT_ANSWER,
    })
    assert r2.status_code == 200
    d2 = r2.json()

    if topic_that_was_covered:
        assert topic_that_was_covered in d2["topics_covered_so_far"], (
            f"Expected '{topic_that_was_covered}' in covered topics, "
            f"got {d2['topics_covered_so_far']}"
        )


# ---------------------------------------------------------------------------
# TC-RESP-06: Session completes after max turns
# ---------------------------------------------------------------------------

def test_respond_session_completes_after_max_turns():
    """
    After MAX_INTERVIEW_QUESTIONS answer submissions via /respond,
    is_complete must be True.
    """
    sid = _start_session()
    max_turns = interview_service.MAX_INTERVIEW_QUESTIONS
    is_complete = False

    for i in range(max_turns):
        r = client.post("/api/v1/interview/respond", json={
            "session_id": sid,
            "answer": f"Detailed answer {i+1} with trade-offs, metrics, and failure handling strategies.",
        })
        assert r.status_code == 200
        is_complete = r.json()["is_complete"]

    assert is_complete is True


# ---------------------------------------------------------------------------
# TC-RESP-07: Invalid session returns 404
# ---------------------------------------------------------------------------

def test_respond_invalid_session_returns_404():
    resp = client.post("/api/v1/interview/respond", json={
        "session_id": "does-not-exist-xyz-000",
        "answer": "Some answer.",
    })
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# TC-RESP-08: Empty answer returns 422
# ---------------------------------------------------------------------------

def test_respond_empty_answer_returns_422():
    sid = _start_session()
    resp = client.post("/api/v1/interview/respond", json={
        "session_id": sid,
        "answer": "   ",
    })
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# TC-RESP-09: DB persistence — agent_decisions stored in history_data
# ---------------------------------------------------------------------------

def test_respond_persists_agent_decisions_to_db():
    """
    Each /respond turn should update SessionHistory.history_data
    with the agent_decisions list.
    """
    from app.db.session import SessionLocal
    from app.models.db_models import SessionHistory

    sid = _start_session()

    client.post("/api/v1/interview/respond", json={
        "session_id": sid,
        "answer": SHORT_ANSWER,
    })

    session = interview_service.get_session(sid)
    assert session is not None and session.db_session_id is not None

    db = SessionLocal()
    try:
        record = db.query(SessionHistory).filter(
            SessionHistory.id == session.db_session_id
        ).first()
        assert record is not None
        assert "agent_decisions" in record.history_data
        assert len(record.history_data["agent_decisions"]) >= 1

        decision_entry = record.history_data["agent_decisions"][0]
        assert "decision" in decision_entry
        assert "answer_quality" in decision_entry
        assert "reasoning" in decision_entry
    finally:
        db.close()


# ---------------------------------------------------------------------------
# TC-RESP-10: /respond does not interfere with /answer on same session
# ---------------------------------------------------------------------------

def test_respond_and_answer_operate_independently():
    """
    Two sessions started independently should not share topic or probe state.
    One using /answer and one using /respond should be fully isolated.
    """
    sid_answer = _start_session()
    sid_respond = _start_session()

    # Submit via /answer on session 1
    r_a = client.post("/api/v1/interview/answer", json={
        "session_id": sid_answer,
        "answer": "I built a REST API with FastAPI.",
    })
    assert r_a.status_code == 200

    # Submit via /respond on session 2
    r_r = client.post("/api/v1/interview/respond", json={
        "session_id": sid_respond,
        "answer": SHORT_ANSWER,
    })
    assert r_r.status_code == 200

    # Session 1 state unaffected by session 2
    s1 = interview_service.get_session(sid_answer)
    s2 = interview_service.get_session(sid_respond)
    assert s1.question_count == 2
    assert s2.question_count == 2
    assert s1.agent_decisions == []   # /answer doesn't populate agent_decisions
    assert len(s2.agent_decisions) == 1


# ---------------------------------------------------------------------------
# TC-RESP-11: Unit — JD competency extraction with keyword matching
# ---------------------------------------------------------------------------

def test_jd_competency_extraction_keyword_matching():
    """
    JD text containing Kafka, Redis, Prometheus, and vector database keywords
    should extract the matching competency labels.
    """
    jd = "We use Kafka for streaming, Redis for caching, Prometheus for observability, and Pinecone as vector DB."
    competencies = _extract_jd_competencies(jd, "Backend Engineer", "Technical")
    assert len(competencies) > 0
    labels = " ".join(competencies).lower()
    assert any(kw in labels for kw in ["kafka", "streaming", "queue"]) or \
           any("message" in c for c in competencies), f"Kafka not extracted: {competencies}"
    assert any("cach" in c.lower() or "redis" in c.lower() for c in competencies), \
           f"Redis not extracted: {competencies}"


# ---------------------------------------------------------------------------
# TC-RESP-12: Unit — JD competency extraction fallback without JD
# ---------------------------------------------------------------------------

def test_jd_competency_extraction_fallback_without_jd():
    """Without a JD, should fall back to role-inferred defaults."""
    competencies = _extract_jd_competencies(None, "ML Engineer", "Technical")
    assert isinstance(competencies, list)
    assert len(competencies) > 0
    # ML-related defaults should be present for ML role
    combined = " ".join(competencies).lower()
    assert any(kw in combined for kw in ["ml", "model", "feature", "vector", "rag", "embedding"])


# ---------------------------------------------------------------------------
# TC-RESP-13: Unit — deterministic agent: short answer → probe
# ---------------------------------------------------------------------------

def test_deterministic_agent_short_answer_probes():
    """Deterministic agent should probe on a very short answer."""
    svc = InterviewService()
    req = InterviewInitRequest(
        candidate_name="Test", target_role="Backend Engineer",
        skill_level="Intermediate", interview_type="Technical",
    )
    session, _ = svc.create_session(req)
    session.history.append({"role": "candidate", "text": "I used a database."})

    result = _deterministic_agent_decision(session, "I used a database.")
    assert result["decision"] == "probe"
    assert result["answer_quality"] in ("weak", "incomplete")
    assert result["probe_target"] is not None
    assert len(result["question"]) > 10


# ---------------------------------------------------------------------------
# TC-RESP-14: Unit — deterministic agent: thorough answer → transition
# ---------------------------------------------------------------------------

def test_deterministic_agent_thorough_answer_transitions():
    """Deterministic agent should transition on a detailed, keyword-rich answer."""
    svc = InterviewService()
    req = InterviewInitRequest(
        candidate_name="Test", target_role="System Architect",
        skill_level="Senior", interview_type="Technical",
    )
    session, _ = svc.create_session(req)

    result = _deterministic_agent_decision(session, THOROUGH_ANSWER)
    assert result["decision"] == "transition"
    assert result["answer_quality"] in ("strong", "adequate")
    assert result["next_topic"] is not None


# ---------------------------------------------------------------------------
# TC-RESP-15: Unit — JSON parser handles malformed and fenced responses
# ---------------------------------------------------------------------------

def test_parse_llm_json_handles_markdown_fences():
    raw_fenced = '```json\n{"decision": "probe", "question": "Tell me more."}\n```'
    parsed = _parse_llm_json(raw_fenced)
    assert parsed is not None
    assert parsed["decision"] == "probe"


def test_parse_llm_json_handles_plain_json():
    raw = '{"decision": "transition", "question": "New topic."}'
    parsed = _parse_llm_json(raw)
    assert parsed is not None
    assert parsed["decision"] == "transition"


def test_parse_llm_json_returns_none_on_garbage():
    parsed = _parse_llm_json("This is not JSON at all.")
    assert parsed is None
