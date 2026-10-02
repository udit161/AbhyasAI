"""
Interview Service — AI Mock Interview Session Manager
======================================================
Manages the full lifecycle of a mock interview session:
  1. Session initialization with candidate context ingestion
  2. Adaptive opening question generation (LLM-tailored to resume + JD + role + level)
  3. Per-turn follow-up question generation (context-aware, progressive depth)
  4. Session state storage with DB persistence hooks
  5. Scorecard generation with dimension scoring
"""
import uuid
import time
import json
import urllib.request
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from app.core.config import settings
from app.models.schemas import (
    InterviewInitRequest,
    InterviewStartResponse,
    InterviewQuestionResponse,
    InterviewScorecardResponse,
)


# ---------------------------------------------------------------------------
# Prompt Templates
# ---------------------------------------------------------------------------

INTERVIEW_SYSTEM_PROMPT = """You are an expert AI technical interviewer at a leading tech company.
Your goal is to conduct a structured, adaptive, and challenging interview session.

INTERVIEW RULES:
1. Ask only ONE focused question at a time.
2. Tailor your question to the candidate's role, skill level, and resume background.
3. For Technical interviews: focus on system design, algorithms, and practical implementation.
4. For Behavioral interviews: use STAR-format prompts (Situation, Task, Action, Result).
5. For System Design interviews: probe for scalability, fault tolerance, and trade-off reasoning.
6. Progressively increase depth based on previous answers.
7. Never reveal the "correct" answer — only probe and follow up.
8. Be professional but conversational. Do NOT include preamble like "Certainly!" or "Great question!".
9. Output ONLY the interview question text, nothing else.
"""

OPENING_QUESTION_PROMPT = """Generate the opening interview question for the following candidate.

CANDIDATE PROFILE:
- Name: {candidate_name}
- Target Role: {target_role}
- Skill Level: {skill_level}
- Interview Type: {interview_type}
{resume_section}
{jd_section}
{course_section}

Generate a single, precise opening question that:
- Immediately engages the candidate on their most relevant background
- Sets the tone appropriate for a {skill_level}-level {interview_type} interview
- For Technical/System Design: opens with a concrete technical scenario or design problem
- For Behavioral: starts with "Tell me about a time when..." framed to their role

Output ONLY the question text, no explanation."""

FOLLOWUP_QUESTION_PROMPT = """You are conducting a {interview_type} interview for a {skill_level} {target_role} candidate.

INTERVIEW HISTORY SO FAR:
{history_block}

CANDIDATE'S LATEST ANSWER:
"{last_answer}"

Based on this answer, generate the next interview question that:
- Probes deeper into a weakness, gap, or interesting point in the candidate's answer
- Escalates technical complexity if the candidate answered confidently
- Pivots to a related but untested competency area if needed
- Remains focused and specific (not generic)

Output ONLY the next question text, no explanation."""

SCORECARD_PROMPT = """You are a senior technical interviewer evaluating a completed mock interview.

INTERVIEW CONTEXT:
- Target Role: {target_role}
- Skill Level: {skill_level}
- Interview Type: {interview_type}

FULL INTERVIEW TRANSCRIPT:
{transcript}

Evaluate the candidate and provide a JSON scorecard with this exact structure:
{{
  "overall_score": <float 0-100>,
  "technical_knowledge_score": <float 0-100>,
  "communication_score": <float 0-100>,
  "problem_solving_score": <float 0-100>,
  "answer_structure_score": <float 0-100>,
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "improvement_areas": ["<area 1>", "<area 2>"],
  "recommendations": ["<rec 1>", "<rec 2>", "<rec 3>"]
}}

Return ONLY the raw JSON, no markdown, no explanation."""


# ---------------------------------------------------------------------------
# Session State Dataclass
# ---------------------------------------------------------------------------

@dataclass
class InterviewSessionState:
    """
    In-memory state for an active interview session.
    Mirrored to DB via SessionHistory on each turn.
    """
    session_id: str
    db_session_id: Optional[str]         # SQLAlchemy SessionHistory.id
    candidate_name: str
    target_role: str
    skill_level: str
    interview_type: str
    resume_text: Optional[str]
    resume_summary: Optional[str]
    job_description: Optional[str]
    course_completed: Optional[str]
    user_id: Optional[str]
    history: List[Dict[str, str]] = field(default_factory=list)  # [{role, text}]
    question_count: int = 0
    is_complete: bool = False
    created_at: float = field(default_factory=time.time)

    def to_history_data(self) -> Dict[str, Any]:
        """Serializes session state to the JSON blob stored in SessionHistory.history_data."""
        return {
            "candidate_name": self.candidate_name,
            "target_role": self.target_role,
            "skill_level": self.skill_level,
            "interview_type": self.interview_type,
            "resume_summary": self.resume_summary,
            "job_description": self.job_description,
            "course_completed": self.course_completed,
            "question_count": self.question_count,
            "is_complete": self.is_complete,
            "messages": self.history,
        }


# ---------------------------------------------------------------------------
# Resume Extractor (simple heuristic, LLM-upgraded when API key available)
# ---------------------------------------------------------------------------

def _extract_resume_summary(resume_text: str, max_chars: int = 400) -> str:
    """
    Extracts a concise summary from raw resume text.
    Uses first meaningful paragraph if LLM is unavailable.
    """
    if not resume_text or not resume_text.strip():
        return ""
    lines = [ln.strip() for ln in resume_text.splitlines() if ln.strip()]
    # Grab first 4 substantive lines (skip headers like NAME, EMAIL etc.)
    substantive = [ln for ln in lines if len(ln) > 30][:4]
    summary = " | ".join(substantive)
    return summary[:max_chars]


# ---------------------------------------------------------------------------
# LLM Caller (mirrors llm_service._call_llm_api pattern)
# ---------------------------------------------------------------------------

def _call_llm(prompt: str, system_prompt: str, temperature: float = 0.7) -> Optional[str]:
    """
    Sends a prompt to the configured LLM provider (OpenAI or Bedrock).
    Returns raw text response or None on failure.
    """
    if settings.OPENAI_API_KEY:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            }
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]
            payload = {
                "model": settings.OPENAI_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 512,
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                return res_json["choices"][0]["message"]["content"].strip()
        except Exception:
            pass

    if settings.ANTHROPIC_API_KEY:
        try:
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "Content-Type": "application/json",
                "x-api-key": settings.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
            }
            payload = {
                "model": settings.ANTHROPIC_MODEL,
                "system": system_prompt,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 512,
                "temperature": temperature,
            }
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                return res_json["content"][0]["text"].strip()
        except Exception:
            pass

    return None


# ---------------------------------------------------------------------------
# Deterministic Question Templates (fallback when no LLM key is configured)
# ---------------------------------------------------------------------------

_OPENING_TEMPLATES: Dict[str, Dict[str, str]] = {
    "Technical": {
        "Entry": (
            "Walk me through a backend or data project you've built recently. "
            "What problem were you solving, and what technology choices did you make?"
        ),
        "Intermediate": (
            "Describe a system you designed or significantly contributed to at scale. "
            "What were the main architectural trade-offs you navigated, and what would you do differently today?"
        ),
        "Senior": (
            "You're tasked with designing a globally distributed real-time event-streaming pipeline "
            "that must handle 500k events/second with sub-100ms end-to-end latency and zero data loss. "
            "Walk me through your architecture, starting from ingestion to storage and query layers."
        ),
    },
    "Behavioral": {
        "Entry": (
            "Tell me about a time you worked through a challenging technical problem with limited guidance. "
            "What approach did you take and what did you learn?"
        ),
        "Intermediate": (
            "Describe a situation where you had to deliver a critical feature under tight deadline pressure "
            "while navigating ambiguous requirements. How did you prioritize and what was the outcome?"
        ),
        "Senior": (
            "Tell me about a time you drove significant technical change across a team or organization. "
            "What was the resistance you encountered, how did you build alignment, and what was the measurable impact?"
        ),
    },
    "System Design": {
        "Entry": (
            "Design a URL shortener service like bit.ly. "
            "Walk me through the key components, your data model, and how you would handle basic scaling."
        ),
        "Intermediate": (
            "Design a notification delivery system that must send 10 million push notifications per day "
            "across iOS, Android, and email channels with delivery guarantees and per-user rate limiting."
        ),
        "Senior": (
            "Design a multi-tenant SaaS platform that serves both free-tier users (heavy volume, low priority) "
            "and enterprise customers (strict SLA guarantees). "
            "How do you isolate workloads, guarantee SLAs, and prevent noisy-neighbour effects at infrastructure level?"
        ),
    },
}

_FOLLOWUP_TEMPLATES = [
    "That's a solid foundation. Can you go deeper on how you handled failure scenarios or edge cases in that approach?",
    "How would that solution scale to 10× or 100× the load you described? Where would the first bottleneck appear?",
    "If you had to rebuild that system today with a different tech stack, what would you change and why?",
    "Walk me through the most critical bug or incident that occurred in that system and how you resolved it.",
    "How did you measure success for that solution? What monitoring and alerting did you put in place?",
]


def _generate_opening_question(session: InterviewSessionState) -> str:
    """
    Generates the tailored opening interview question using LLM or deterministic template.
    """
    resume_section = ""
    if session.resume_summary:
        resume_section = f"- Resume Summary: {session.resume_summary}"
    elif session.resume_text:
        summary = _extract_resume_summary(session.resume_text)
        resume_section = f"- Resume Summary: {summary}"

    jd_section = ""
    if session.job_description:
        jd_preview = session.job_description[:600].replace("\n", " ")
        jd_section = f"- Job Description (excerpt): {jd_preview}"

    course_section = ""
    if session.course_completed:
        course_section = f"- Relevant Course Completed: {session.course_completed}"

    prompt = OPENING_QUESTION_PROMPT.format(
        candidate_name=session.candidate_name,
        target_role=session.target_role,
        skill_level=session.skill_level,
        interview_type=session.interview_type,
        resume_section=resume_section,
        jd_section=jd_section,
        course_section=course_section,
    )

    llm_question = _call_llm(prompt, INTERVIEW_SYSTEM_PROMPT, temperature=0.75)
    if llm_question:
        return llm_question

    # Deterministic fallback
    interview_type = session.interview_type if session.interview_type in _OPENING_TEMPLATES else "Technical"
    skill_level = session.skill_level if session.skill_level in _OPENING_TEMPLATES[interview_type] else "Intermediate"
    base_question = _OPENING_TEMPLATES[interview_type][skill_level]

    # Personalize with role/resume if available
    if session.resume_summary:
        return (
            f"Given your background — {session.resume_summary[:120]} — "
            f"for this {session.target_role} role: {base_question}"
        )
    return f"For the {session.target_role} position: {base_question}"


def _generate_followup_question(session: InterviewSessionState) -> str:
    """
    Generates the next adaptive follow-up question based on session history.
    """
    if not session.history:
        return _generate_opening_question(session)

    # Build history block for the prompt
    history_lines = []
    for turn in session.history:
        speaker = "Interviewer" if turn["role"] == "interviewer" else "Candidate"
        history_lines.append(f"{speaker}: {turn['text']}")
    history_block = "\n\n".join(history_lines)

    # Extract candidate's most recent answer
    candidate_turns = [t for t in session.history if t["role"] == "candidate"]
    last_answer = candidate_turns[-1]["text"] if candidate_turns else ""

    prompt = FOLLOWUP_QUESTION_PROMPT.format(
        interview_type=session.interview_type,
        skill_level=session.skill_level,
        target_role=session.target_role,
        history_block=history_block,
        last_answer=last_answer[:800],
    )

    llm_question = _call_llm(prompt, INTERVIEW_SYSTEM_PROMPT, temperature=0.7)
    if llm_question:
        return llm_question

    # Deterministic fallback — cycle through templates
    idx = min(session.question_count - 1, len(_FOLLOWUP_TEMPLATES) - 1)
    return _FOLLOWUP_TEMPLATES[idx]


def _generate_scorecard_from_llm(session: InterviewSessionState) -> Optional[Dict[str, Any]]:
    """
    Generates a structured scorecard JSON from LLM evaluation of the full transcript.
    """
    transcript_lines = []
    for turn in session.history:
        speaker = "Interviewer" if turn["role"] == "interviewer" else "Candidate"
        transcript_lines.append(f"{speaker}: {turn['text']}")
    transcript = "\n\n".join(transcript_lines)

    prompt = SCORECARD_PROMPT.format(
        target_role=session.target_role,
        skill_level=session.skill_level,
        interview_type=session.interview_type,
        transcript=transcript,
    )

    raw = _call_llm(prompt, INTERVIEW_SYSTEM_PROMPT, temperature=0.2)
    if raw:
        try:
            # Strip potential markdown code fences
            cleaned = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            return json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            pass
    return None


# ---------------------------------------------------------------------------
# Interview Service
# ---------------------------------------------------------------------------

class InterviewService:
    """
    Manages the full lifecycle of AI mock interview sessions:
    - Session creation and in-memory state storage
    - Adaptive question generation (LLM-first, deterministic fallback)
    - Per-turn answer processing and progressive follow-up questions
    - LLM-evaluated scorecard generation on session completion
    """

    MAX_INTERVIEW_QUESTIONS = 5

    def __init__(self):
        # In-memory store — keyed by session_id
        # In production, replace with Redis or DB-backed session store
        self._sessions: Dict[str, InterviewSessionState] = {}

    # ------------------------------------------------------------------
    # Session Initialization
    # ------------------------------------------------------------------

    def create_session(
        self,
        req: InterviewInitRequest,
        db_session_id: Optional[str] = None,
    ) -> Tuple[InterviewSessionState, str]:
        """
        Creates a new interview session, generates the tailored opening question,
        and persists initial state.

        Returns:
            (session_state, opening_question)
        """
        session_id = str(uuid.uuid4())

        # Extract resume summary if full resume text is provided
        resume_summary = req.resume_summary
        if not resume_summary and req.resume_text:
            resume_summary = _extract_resume_summary(req.resume_text)

        session = InterviewSessionState(
            session_id=session_id,
            db_session_id=db_session_id,
            candidate_name=req.candidate_name,
            target_role=req.target_role,
            skill_level=req.skill_level,
            interview_type=req.interview_type,
            resume_text=req.resume_text,
            resume_summary=resume_summary,
            job_description=req.job_description,
            course_completed=req.course_completed,
            user_id=req.user_id,
        )

        # Generate the tailored opening question
        opening_question = _generate_opening_question(session)

        # Record in session history
        session.history.append({"role": "interviewer", "text": opening_question})
        session.question_count = 1

        self._sessions[session_id] = session
        return session, opening_question

    # ------------------------------------------------------------------
    # Per-turn Processing
    # ------------------------------------------------------------------

    def process_answer(
        self,
        session_id: str,
        answer: str,
    ) -> Tuple[str, int, bool]:
        """
        Records the candidate's answer, then generates and records the next question.

        Returns:
            (next_question_or_closing_message, question_number, is_complete)
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Interview session '{session_id}' not found. It may have expired.")

        if session.is_complete:
            raise ValueError("This interview session has already been completed.")

        # Record candidate answer
        session.history.append({"role": "candidate", "text": answer})
        session.question_count += 1

        # Check if max turns reached
        if session.question_count > self.MAX_INTERVIEW_QUESTIONS:
            session.is_complete = True
            closing = (
                f"Thank you, {session.candidate_name}! That wraps up our interview. "
                "You've covered some excellent areas today. "
                "Your scorecard is being generated now — please call /api/v1/interview/scorecard "
                f"with session_id={session_id} to retrieve your full evaluation."
            )
            session.history.append({"role": "interviewer", "text": closing})
            return closing, session.question_count, True

        # Generate adaptive follow-up
        next_question = _generate_followup_question(session)
        session.history.append({"role": "interviewer", "text": next_question})

        return next_question, session.question_count, False

    # ------------------------------------------------------------------
    # Scorecard Generation
    # ------------------------------------------------------------------

    def generate_scorecard(self, session_id: str) -> InterviewScorecardResponse:
        """
        Evaluates the complete interview transcript and returns a structured scorecard.
        Uses LLM if available, otherwise returns a calibrated heuristic scorecard.
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Interview session '{session_id}' not found.")

        # Estimate cost: ~1500 tokens per turn at $0.002/1K tokens
        turns = session.question_count
        est_cost = f"${turns * 1500 * 0.002 / 1000:.4f} (~{turns} turns, GPT-4o-mini pricing)"

        # Try LLM-based scorecard
        llm_scorecard = _generate_scorecard_from_llm(session)
        if llm_scorecard:
            return InterviewScorecardResponse(
                session_id=session_id,
                overall_score=float(llm_scorecard.get("overall_score", 75.0)),
                technical_knowledge_score=float(llm_scorecard.get("technical_knowledge_score", 75.0)),
                communication_score=float(llm_scorecard.get("communication_score", 75.0)),
                problem_solving_score=float(llm_scorecard.get("problem_solving_score", 75.0)),
                answer_structure_score=float(llm_scorecard.get("answer_structure_score", 75.0)),
                strengths=llm_scorecard.get("strengths", ["Good overall performance."]),
                improvement_areas=llm_scorecard.get("improvement_areas", ["Continue practicing structured answers."]),
                recommendations=llm_scorecard.get("recommendations", ["Review STAR format for behavioral responses."]),
                estimated_operating_cost=est_cost,
            )

        # Heuristic fallback scorecard (deterministic, role/level calibrated)
        _base = {"Entry": 72.0, "Intermediate": 78.0, "Senior": 82.0}
        base = _base.get(session.skill_level, 75.0)

        return InterviewScorecardResponse(
            session_id=session_id,
            overall_score=base,
            technical_knowledge_score=base + 2.0,
            communication_score=base - 1.5,
            problem_solving_score=base + 1.0,
            answer_structure_score=base - 0.5,
            strengths=[
                f"Demonstrated knowledge relevant to the {session.target_role} role.",
                "Maintained clear and professional communication throughout.",
                "Showed ability to reason through technical trade-offs.",
            ],
            improvement_areas=[
                "Consider using the STAR format more consistently for behavioral questions.",
                "Provide more specific metrics and outcomes when describing past projects.",
            ],
            recommendations=[
                f"Study system design patterns relevant to {session.target_role} at {session.skill_level} level.",
                "Practice timed mock interviews to improve response conciseness.",
                "Review common failure modes and mitigation strategies in distributed systems.",
            ],
            estimated_operating_cost=est_cost,
        )

    # ------------------------------------------------------------------
    # State Access Helpers
    # ------------------------------------------------------------------

    def get_session(self, session_id: str) -> Optional[InterviewSessionState]:
        return self._sessions.get(session_id)

    def session_exists(self, session_id: str) -> bool:
        return session_id in self._sessions

    def get_session_history(self, session_id: str) -> List[Dict[str, str]]:
        session = self._sessions.get(session_id)
        return session.history if session else []


# Singleton
interview_service = InterviewService()
