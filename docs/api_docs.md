# API Specification

## Endpoints

### 1. Learning Assistant Q&A
- **Endpoint**: `POST /api/v1/ask`
- **Description**: Ask timestamp-aware question grounded in watched content.
- **Request Body**:
  ```json
  {
    "video_id": "video_sample_1",
    "current_timestamp": 1122.0,
    "question": "Why did the instructor use this method?"
  }
  ```

### 2. Context Quiz Generator
- **Endpoint**: `POST /api/v1/quiz`
- **Description**: Generate multiple-choice quiz questions from content covered up to current timestamp.

### 3. Start Mock Interview
- **Endpoint**: `POST /api/v1/interview/start`
- **Description**: Initialize interactive adaptive mock interview session.

### 4. Submit Interview Answer
- **Endpoint**: `POST /api/v1/interview/answer`
- **Description**: Submit answer to interviewer and receive adaptive follow-up question.

### 5. Interview Scorecard
- **Endpoint**: `GET /api/v1/interview/scorecard/{session_id}`
- **Description**: Fetch overall score, technical/communication breakdown, strengths, growth areas, and cost metrics.
