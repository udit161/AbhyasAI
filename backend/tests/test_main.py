from fastapi.testclient import TestClient
from app.main import app
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

def test_chat_ask_grounded_rag_request():
    """
    Test POST /chat/ask with valid QuestionRequest returns 200 with grounded RAG answer and citations.
    """
    video_id = "test_main_vid_1"
    vector_store.add_video_segments(
        video_id=video_id,
        title="FastAPI RAG Course",
        segments=[
            {"start_time": 0.0, "end_time": 100.0, "text": "FastAPI uses Pydantic models for data validation and OpenAPI schema generation."}
        ]
    )

    payload = {
        "video_id": video_id,
        "current_timestamp": 125.5,
        "question": "What is FastAPI?",
        "conversation_history": [],
        "allowed_resource_ids": [video_id]
    }
    response = client.post("/chat/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "citations" in data
    assert data["is_refusal"] is False
    assert len(data["citations"]) > 0

def test_chat_ask_refusal_when_unsupported_by_context():
    """
    Test POST /chat/ask returns refusal when query cannot be answered from context.
    """
    video_id = "test_main_vid_2"
    payload = {
        "video_id": video_id,
        "current_timestamp": 10.0,
        "question": "What is quantum thermodynamics?",
        "conversation_history": [],
        "allowed_resource_ids": [video_id]
    }
    response = client.post("/chat/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_refusal"] is True
    assert "refusal_reason" in data
    assert "do not know" in data["answer"].lower()

def test_chat_ask_validation_missing_field():
    """
    Test POST /chat/ask fails with 422 when required fields are missing.
    """
    payload = {
        "video_id": "video_fastapi_intro"
        # missing current_timestamp and question
    }
    response = client.post("/chat/ask", json=payload)
    assert response.status_code == 422
