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
    """
    Request schema for starting a new AI mock interview session.
    Accepts candidate background, JD, role, and skill level for
    adaptive opening question generation.
    """
    candidate_name: str = Field(..., min_length=1, description="Full name of the candidate")
    target_role: str = Field(..., min_length=1, description="Job role being interviewed for (e.g. 'Senior ML Engineer')")
    job_description: Optional[str] = Field(None, description="Full job description text for adaptive tailoring")
    resume_text: Optional[str] = Field(None, description="Candidate full resume text for deeper context")
    resume_summary: Optional[str] = Field(None, description="Short resume summary (auto-extracted if resume_text is provided)")
    course_completed: Optional[str] = Field(None, description="Name of course/curriculum the candidate has completed")
    skill_level: str = Field("Intermediate", description="Candidate level: Entry, Intermediate, or Senior")
    interview_type: str = Field("Technical", description="Interview type: Technical, Behavioral, or System Design")
    user_id: Optional[str] = Field(None, description="Optional authenticated user ID for session persistence")


class InterviewStartResponse(BaseModel):
    """
    Response schema returned after POST /api/v1/interview/start.
    Contains the DB session ID and the tailored opening question.
    """
    session_id: str = Field(..., description="Unique DB-persisted session ID for subsequent turn API calls")
    candidate_name: str
    target_role: str
    skill_level: str
    interview_type: str
    question_number: int = Field(default=1, description="Always 1 for the opening question")
    opening_question: str = Field(..., description="AI-generated opening interview question tailored to candidate")
    resume_summary_used: Optional[str] = Field(None, description="Extracted resume summary the AI used for tailoring")
    estimated_turns: int = Field(default=5, description="Estimated number of interview questions in the session")


class InterviewQuestionResponse(BaseModel):
    session_id: str
    question_number: int
    question: str
    is_complete: bool = False
    audio_url: Optional[str] = None

class CandidateAnswerRequest(BaseModel):
    session_id: str
    answer: str

class InterviewScorecardRequest(BaseModel):
    session_id: str = Field(..., description="Active or completed interview session ID")

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



class InterviewRespondRequest(BaseModel):
    """
    Request schema for POST /api/v1/interview/respond.
    The candidate's latest answer is analyzed by the LLM agent which
    dynamically decides whether to probe deeper or transition topics.
    """
    session_id: str = Field(..., description="Active interview session ID")
    answer: str = Field(..., min_length=1, description="Candidate's answer to the current question")


class InterviewRespondResponse(BaseModel):
    """
    Response schema for POST /api/v1/interview/respond.
    Exposes the agent's full decision trace alongside the next question.
    """
    session_id: str
    question_number: int = Field(..., description="Ordinal number of the next question in the session")
    question: str = Field(..., description="The next interview question generated by the agent")

    # Agent decision metadata
    decision: str = Field(
        ...,
        description="'probe' — drilling deeper into current topic | 'transition' — moving to a new competency",
    )
    reasoning: str = Field(..., description="Agent's 1-2 sentence rationale for the decision")
    answer_quality: str = Field(
        ...,
        description="Agent's assessment: 'strong' | 'adequate' | 'weak' | 'incomplete'",
    )
    probe_target: Optional[str] = Field(
        None,
        description="Specific gap or aspect being probed (populated when decision='probe')",
    )

    # Topic coverage tracking
    topic_covered: Optional[str] = Field(
        None,
        description="Competency area the candidate just demonstrated",
    )
    next_topic: Optional[str] = Field(
        None,
        description="Competency area the agent is transitioning to (populated when decision='transition')",
    )
    topics_covered_so_far: List[str] = Field(
        default_factory=list,
        description="Cumulative list of JD competency areas explored so far",
    )
    topics_remaining: List[str] = Field(
        default_factory=list,
        description="JD competency areas not yet covered in this session",
    )

    is_complete: bool = Field(default=False, description="True when the interview session is finished")
    latency_ms: float = Field(default=0.0, description="Agent decision + question generation latency")

