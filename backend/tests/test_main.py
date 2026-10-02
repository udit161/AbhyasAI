from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.db_models import User, SessionHistory
from app.db.vector_store import vector_store

client = TestClient(app)

def test_health_check_endpoint():
    """
    Test GET /health returns status 200 and {"status": "ok"}.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_root_endpoint():
    """
    Test GET / returns welcome message and docs links.
    """
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "project" in data
    assert data["documentation"] == "/docs"

def test_api_v1_chat_session_endpoint_persists_to_db():
    """
    Test POST /api/v1/chat accepts user_id, video_id, current_timestamp, query,
    executes vector search, generates grounded RAG answer, saves history to DB, and returns citations.
    """
    import uuid
    db = SessionLocal()
    user = db.query(User).filter(User.email == "test_chat_user@abhyas.ai").first()
    if not user:
        user = User(email="test_chat_user@abhyas.ai", full_name="Chat Test User", hashed_password="pw")
        db.add(user)
        db.commit()
        db.refresh(user)


    video_id = "vid_chat_api_1"
    vector_store.add_video_segments(
        video_id=video_id,
        title="Python FastAPI & Vector Databases",
        segments=[
            {"start_time": 0.0, "end_time": 120.0, "text": "FastAPI endpoints process Pydantic models and return JSON responses."}
        ]
    )

    payload = {
        "user_id": user.id,
        "video_id": video_id,
        "current_timestamp": 125.0,
        "query": "How does FastAPI process requests?",
        "permitted_doc_ids": []
    }


    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["session_id"] is not None
    assert data["user_id"] == user.id
    assert data["video_id"] == video_id
    assert "answer" in data
    assert len(data["citations"]) > 0

    # Verify session interaction record was saved in relational DB
    db_session_record = db.query(SessionHistory).filter(SessionHistory.id == data["session_id"]).first()
    assert db_session_record is not None
    assert db_session_record.user_id == user.id
    assert db_session_record.session_type == "chat"
    assert db_session_record.history_data["query"] == "How does FastAPI process requests?"

    db.close()

def test_chat_ask_refusal_when_unsupported_by_context():
    """
    Test POST /api/v1/chat returns refusal when query cannot be answered from context.
    """
    video_id = "test_main_vid_2"
    payload = {
        "user_id": "usr_unknown_1",
        "video_id": video_id,
        "current_timestamp": 10.0,
        "query": "What is quantum thermodynamics?",
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_refusal"] is True
    assert data["refusal_reason"] is not None
    assert "do not know" in data["answer"].lower()

def test_chat_ask_validation_missing_field():
    """
    Test POST /api/v1/chat fails with 422 when required fields are missing.
    """
    payload = {
        "video_id": "video_fastapi_intro"
        # missing user_id, current_timestamp and query
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 422
