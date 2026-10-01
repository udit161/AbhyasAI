# AI Learning Assistant - Phase 1 Backend

Welcome to **Phase 1** of the **AI Learning Assistant** backend! This project is built using **Python** and **FastAPI**, designed to serve interactive video learning platforms.

---

## 📁 Project Folder Structure & Explanation

```text
backend/
├── app/
│   ├── __init__.py         # Marks 'app' as a Python package
│   ├── main.py             # Entry point: initializes FastAPI app, CORS, and routers
│   ├── schemas.py          # Pydantic models for request validation & response schemas
│   └── routers/
│       ├── __init__.py     # Marks 'routers' as a Python package
│       ├── health.py       # GET /health endpoint for server status checks
│       └── chat.py         # POST /chat/ask endpoint accepting Q&A requests & returning mock responses
├── tests/
│   ├── __init__.py         # Marks 'tests' as a Python package
│   └── test_main.py        # Automated test suite using Pytest and FastAPI TestClient
├── .gitignore              # Ignores virtualenv, cache, and sensitive files from git
├── requirements.txt        # List of Python dependencies (FastAPI, Uvicorn, Pydantic, pytest, httpx)
└── README.md               # Beginner-friendly guide and documentation
```

### 📄 Detailed Explanation of Every File:

1. **`app/main.py`**:
   - The heart of the FastAPI application.
   - Sets up the FastAPI app instance with metadata (`title`, `description`, `version`).
   - Configures **CORS** (Cross-Origin Resource Sharing) so your frontend can communicate with the backend.
   - Includes route modules (`health.py` and `chat.py`).

2. **`app/schemas.py`**:
   - Uses **Pydantic** (`BaseModel`) to validate data sent by clients.
   - `ChatAskRequest`: Guarantees that requests to `/chat/ask` contain valid `course_id`, `video_id`, non-negative `current_timestamp`, and a non-empty `question`.
   - `ChatAskResponse`: Defines the structured JSON output returned to the client.

3. **`app/routers/health.py`**:
   - Contains the `GET /health` route.
   - Returns `{"status": "ok"}` when the API is active.

4. **`app/routers/chat.py`**:
   - Contains the `POST /chat/ask` route.
   - Receives the validated request, constructs a clearly labeled mock AI response, and echoes back course/video metadata.

5. **`tests/test_main.py`**:
   - Contains unit tests written using `pytest` and `TestClient`.
   - Verifies route responses (`200 OK`) and validation failures (`422 Unprocessable Entity`).

6. **`requirements.txt`**:
   - Specifies project dependencies: `fastapi`, `uvicorn`, `pydantic`, `pytest`, `httpx`.

7. **`.gitignore`**:
   - Prevents virtual environment directories (`venv/`), `__pycache__`, and temporary test files from being pushed to Git.

---

## 🚀 Step-by-Step Beginner Guide

### Step 1: Open Terminal in the Backend Folder
```bash
cd backend
```

### Step 2: Set Up Python Virtual Environment
A virtual environment keeps your project dependencies isolated.

**On Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

---

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

---

### Step 4: Run the Development Server
Start the local API server using **Uvicorn**:

```bash
uvicorn app.main:app --reload
```

- Server URL: `http://127.0.0.1:8000`
- Interactive API Docs (Swagger UI): `http://127.0.0.1:8000/docs`
- Alternative API Docs (ReDoc): `http://127.0.0.1:8000/redoc`

---

### Step 5: Test the Endpoints

#### 1. Check Server Health (`GET /health`)
- **URL**: `http://127.0.0.1:8000/health`
- **Response**:
```json
{
  "status": "ok"
}
```

#### 2. Ask a Question (`POST /chat/ask`)
- **URL**: `http://127.0.0.1:8000/chat/ask`
- **Header**: `Content-Type: application/json`
- **Request Body**:
```json
{
  "course_id": "course_101",
  "video_id": "video_202",
  "current_timestamp": 120.5,
  "question": "What is FastAPI?"
}
```
- **Response**:
```json
{
  "status": "success",
  "is_mock": true,
  "message": "[MOCK RESPONSE] AI LLM integration is disabled in Phase 1.",
  "course_id": "course_101",
  "video_id": "video_202",
  "current_timestamp": 120.5,
  "question": "What is FastAPI?",
  "mock_answer": "[MOCK ANSWER] Thank you for asking: 'What is FastAPI?'. This response is simulated for Course 'course_101', Video 'video_202' at timestamp 120.5s."
}
```

---

### Step 6: Run Automated API Tests
Run all unit tests using `pytest`:

```bash
pytest
```
