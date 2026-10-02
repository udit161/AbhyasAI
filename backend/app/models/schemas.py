from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Learning Assistant Schemas
class SourceCitation(BaseModel):
    source_type: str = Field(..., description="video, pdf, ppt, or note")
    resource_id: str
    title: str
    timestamp_start: Optional[float] = Field(None, description="Start timestamp in seconds")
    timestamp_end: Optional[float] = Field(None, description="End timestamp in seconds")
    page_number: Optional[int] = Field(None, description="PDF page or PPT slide number")
    snippet: str = Field(..., description="Grounding text snippet")

class QuestionRequest(BaseModel):
    video_id: str
    current_timestamp: float = Field(..., description="Current video playback time in seconds (e.g. 1122.0 for 18:42)")
    question: str
    conversation_history: Optional[List[Dict[str, str]]] = []
    allowed_resource_ids: Optional[List[str]] = []

class AnswerResponse(BaseModel):
    answer: str
    citations: List[SourceCitation]
    timestamp_range_used: str = Field(..., description="e.g., 00:00 - 18:42")
    is_refusal: bool = False
    refusal_reason: Optional[str] = None
    latency_ms: float

class ChatSessionRequest(BaseModel):
    user_id: str = Field(..., description="ID of the user making the chat request")
    video_id: str = Field(..., description="ID of the active video being watched")
    current_timestamp: float = Field(..., ge=0.0, description="Current video playback timestamp in seconds")
    query: str = Field(..., min_length=1, description="User question or query")
    course_id: Optional[str] = Field(None, description="Optional Course ID")
    permitted_doc_ids: Optional[List[str]] = Field(default=[], description="List of permitted supporting PDF/PPT document IDs")
    conversation_history: Optional[List[Dict[str, str]]] = Field(default=[], description="Optional previous chat history")

class ChatSessionResponse(BaseModel):
    session_id: str = Field(..., description="Database ID of saved session history record")
    user_id: str
    video_id: str
    query: str
    answer: str
    citations: List[SourceCitation]
    timestamp_range_used: str
    is_refusal: bool = False
    refusal_reason: Optional[str] = None
    latency_ms: float


class QuizGenerateRequest(BaseModel):
    video_id: str
    current_timestamp: float
    num_questions: int = 3

class QuizQuestion(BaseModel):
    id: str
    question: str
    options: List[str]
    correct_option_index: int
    explanation: str
    source_citation: Optional[SourceCitation] = None

class QuizResponse(BaseModel):
    video_id: str
    current_timestamp: float
    questions: List[QuizQuestion]

# Ingestion Schemas
class IngestVideoRequest(BaseModel):
    video_id: str
    title: str
    transcript_vt_content: str

class IngestDocumentRequest(BaseModel):
    doc_id: str
    title: str
    doc_type: str # pdf or ppt
    file_path: str

# Mock Interview Schemas
class InterviewInitRequest(BaseModel):
    candidate_name: str
    target_role: str
    job_description: Optional[str] = None
    resume_summary: Optional[str] = None
    course_completed: Optional[str] = None
    skill_level: str = "Intermediate" # Entry, Intermediate, Senior
    interview_type: str = "Technical" # Technical, Behavioral, System Design

class InterviewQuestionResponse(BaseModel):
    session_id: str
    question_number: int
    question: str
    audio_url: Optional[str] = None

class CandidateAnswerRequest(BaseModel):
    session_id: str
    answer: str

class InterviewScorecardResponse(BaseModel):
    session_id: str
    overall_score: float # 0-100
    technical_knowledge_score: float
    communication_score: float
    problem_solving_score: float
    answer_structure_score: float
    strengths: List[str]
    improvement_areas: List[str]
    recommendations: List[str]
    estimated_operating_cost: str
