from fastapi.testclient import TestClient
from app.main import app

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

def test_chat_ask_valid_request():
    """
    Test POST /chat/ask with valid data structure returns 200 and mock answer.
    """
    payload = {
        "course_id": "course_python_101",
        "video_id": "video_fastapi_intro",
        "current_timestamp": 125.5,
        "question": "What is FastAPI and how does Pydantic validate requests?"
    }
    response = client.post("/chat/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["is_mock"] is True
    assert data["course_id"] == "course_python_101"
    assert data["video_id"] == "video_fastapi_intro"
    assert data["current_timestamp"] == 125.5
    assert data["question"] == "What is FastAPI and how does Pydantic validate requests?"
    assert "[MOCK ANSWER]" in data["mock_answer"]

def test_chat_ask_validation_missing_field():
    """
    Test POST /chat/ask fails with 422 when required fields are missing.
    """
    payload = {
        "course_id": "course_python_101",
        "video_id": "video_fastapi_intro"
        # missing current_timestamp and question
    }
    response = client.post("/chat/ask", json=payload)
    assert response.status_code == 422

def test_chat_ask_validation_invalid_type():
    """
    Test POST /chat/ask fails with 422 when current_timestamp is negative.
    """
    payload = {
        "course_id": "course_python_101",
        "video_id": "video_fastapi_intro",
        "current_timestamp": -15.0,
        "question": "Invalid negative timestamp question"
    }
    response = client.post("/chat/ask", json=payload)
    assert response.status_code == 422
