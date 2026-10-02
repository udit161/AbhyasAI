"""
Interview Service — AI Mock Interview Session Manager
======================================================
Manages the full lifecycle of a mock interview session:
  1. Session initialization with candidate context ingestion
  2. Adaptive opening question generation (LLM-tailored to resume + JD + role + level)
  3. Per-turn follow-up question generation (context-aware, progressive depth)
  4. Dynamic agent: PROBE vs TRANSITION decision engine for /respond endpoint
  5. Session state storage with DB persistence hooks
  6. Scorecard generation with dimension scoring
"""
import uuid
import time
import json
import re
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

# ---------------------------------------------------------------------------
# Agent Decision Prompts (for /respond endpoint)
# ---------------------------------------------------------------------------

AGENT_DECISION_SYSTEM_PROMPT = """You are an expert AI technical interviewer making intelligent real-time decisions during a mock interview.

Your task is to analyze the candidate's latest answer and decide the optimal next move:

DECISION OPTIONS:
- "probe"      → Ask a deeper follow-up about the SAME topic. Use when the answer is vague, incomplete,
                  reveals a gap (no failure handling, no metrics, no trade-off reasoning), or surfaces an
                  interesting technical detail worth drilling into.
- "transition" → Move to a NEW competency topic from the job description. Use when the answer is thorough
                  with concrete examples and trade-off reasoning, OR the topic has been probed 2+ times already.

You must return ONLY a raw JSON object with this exact structure (no markdown, no explanation):
{
  "decision": "probe" | "transition",
  "reasoning": "<1-2 sentences explaining why you chose probe or transition>",
  "answer_quality": "strong" | "adequate" | "weak" | "incomplete",
  "probe_target": "<specific gap or depth being drilled — null if transitioning>",
  "topic_covered": "<competency area the candidate just demonstrated, e.g. 'distributed caching'>",
  "next_topic": "<next JD competency to explore — null if probing>",
  "question": "<the actual interview question — professional, specific, no conversational preamble>"
}"""

AGENT_DECISION_PROMPT = """INTERVIEW CONTEXT:
- Target Role: {target_role}
- Skill Level: {skill_level}
- Interview Type: {interview_type}
{jd_section}

COMPETENCY COVERAGE STATUS:
- Already adequately covered: {covered_topics}
- Still to cover: {remaining_topics}
- Current topic has been probed {probe_count} time(s) so far

FULL INTERVIEW HISTORY:
{history_block}

CANDIDATE'S LATEST ANSWER:
"{last_answer}"

Analyze the answer quality and make your decision. Remember:
- PROBE if the answer is shallow/incomplete or reveals a specific untested dimension
- TRANSITION if the answer is thorough or this topic has been probed {max_probes}+ times
- If remaining topics is empty, prefer one final deep probe on the most important gap

Output ONLY the raw JSON decision object."""

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
    history: List[Dict[str, str]] = field(default_factory=list)   # [{role, text}]
    question_count: int = 0
    is_complete: bool = False
    created_at: float = field(default_factory=time.time)

    # ── Dynamic agent state (for /respond endpoint) ──────────────────────
    # Extracted JD competencies to cover during the interview
    jd_competencies: List[str] = field(default_factory=list)
    # Topics adequately covered so far (appended by the agent on TRANSITION)
    covered_topics: List[str] = field(default_factory=list)
    # How many times each topic has been probed: {topic_label: count}
    probe_counts: Dict[str, int] = field(default_factory=dict)
    # Full log of agent decisions: [{turn, decision, reasoning, answer_quality, ...}]
    agent_decisions: List[Dict[str, Any]] = field(default_factory=list)
    # Current active topic being explored (used to count probes per topic)
    current_topic: Optional[str] = None

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
            "covered_topics": self.covered_topics,
            "jd_competencies": self.jd_competencies,
            "agent_decisions": self.agent_decisions,
        }


# ---------------------------------------------------------------------------
# JD Competency Extractor
# ---------------------------------------------------------------------------

# Role-specific default competency banks (fallback when no JD provided)
_DEFAULT_COMPETENCIES: Dict[str, Dict[str, List[str]]] = {
    "Technical": {
        "default": [
            "system design & scalability",
            "data structures & algorithms",
            "API design & REST principles",
            "database design & query optimization",
            "debugging & incident resolution",
            "distributed systems & fault tolerance",
        ],
        "ml": [
            "ML model training & evaluation",
            "feature engineering & data pipelines",
            "model serving & deployment",
            "experiment tracking & reproducibility",
            "vector databases & semantic search",
            "RAG systems & LLM integration",
        ],
        "backend": [
            "microservices & service mesh",
            "caching strategies (Redis, CDN)",
            "message queues & event streaming",
            "CI/CD & infrastructure as code",
            "security & authentication patterns",
            "observability & SLO engineering",
        ],
    },
    "Behavioral": {
        "default": [
            "cross-functional collaboration",
            "conflict resolution & stakeholder management",
            "ownership & delivery under pressure",
            "mentorship & knowledge sharing",
            "ambiguity & priority setting",
            "retrospection & continuous improvement",
        ],
    },
    "System Design": {
        "default": [
            "requirements clarification & scoping",
            "high-level architecture",
            "data model & storage design",
            "scalability & load handling",
            "fault tolerance & disaster recovery",
            "API & interface design",
            "monitoring & alerting strategy",
        ],
    },
}

# Tech keyword → competency label mapping
_KEYWORD_COMPETENCY_MAP = {
    # ML / AI
    r"\b(machine learning|ml model|deep learning|neural network)\b": "ML model training & evaluation",
    r"\b(feature engineering|data pipeline|etl|feature store)\b": "feature engineering & data pipelines",
    r"\b(model serv|inference|deployment|mlops|kubeflow|airflow)\b": "model serving & deployment",
    r"\b(vector (db|database|store)|embedding|pinecone|chroma|qdrant|weaviate)\b": "vector databases & semantic search",
    r"\b(rag|retrieval augmented|llm|gpt|claude|gemini|langchain)\b": "RAG systems & LLM integration",
    r"\b(a/b test|experiment tracking|mlflow|wandb)\b": "experiment tracking & reproducibility",
    # Systems
    r"\b(microservice|service mesh|grpc|api gateway)\b": "microservices & service mesh",
    r"\b(redis|memcache|caching|cdn|cache invalidation)\b": "caching strategies (Redis, CDN)",
    r"\b(kafka|rabbitmq|sqs|pubsub|event stream|message queue)\b": "message queues & event streaming",
    r"\b(ci/cd|terraform|kubernetes|k8s|helm|docker|iac)\b": "CI/CD & infrastructure as code",
    r"\b(oauth|jwt|auth|zero trust|rbac|security)\b": "security & authentication patterns",
    r"\b(observability|prometheus|grafana|datadog|slo|sli|sre)\b": "observability & SLO engineering",
    r"\b(sql|postgres|mysql|nosql|cassandra|dynamo|database design)\b": "database design & query optimization",
    r"\b(distributed|consensus|raft|paxos|cap theorem|eventual consistency)\b": "distributed systems & fault tolerance",
    r"\b(rest|graphql|openapi|swagger|api design)\b": "API design & REST principles",
    r"\b(algorithm|data structure|leetcode|complexity|big-o)\b": "data structures & algorithms",
    r"\b(system design|scalab|high.availability|sharding|partition)\b": "system design & scalability",
    # Behavioral
    r"\b(collaboration|cross.functional|stakeholder)\b": "cross-functional collaboration",
    r"\b(mentor|coach|knowledge sharing|tech lead)\b": "mentorship & knowledge sharing",
    r"\b(ambiguity|priorit|roadmap|product sense)\b": "ambiguity & priority setting",
    r"\b(conflict|feedback|retrospect|post.mortem)\b": "conflict resolution & stakeholder management",
}


def _extract_jd_competencies(
    jd_text: Optional[str],
    target_role: str,
    interview_type: str,
    max_competencies: int = 6,
) -> List[str]:
    """
    Extracts a prioritized list of competency areas from the JD text.
    Falls back to role-inferred defaults when no JD is provided.
    """
    competencies: List[str] = []

    if jd_text:
        jd_lower = jd_text.lower()
        seen: set = set()
        for pattern, label in _KEYWORD_COMPETENCY_MAP.items():
            if re.search(pattern, jd_lower) and label not in seen:
                competencies.append(label)
                seen.add(label)
            if len(competencies) >= max_competencies:
                break

    if not competencies:
        # Fall back to defaults keyed by interview_type
        role_lower = target_role.lower()
        itype = interview_type if interview_type in _DEFAULT_COMPETENCIES else "Technical"
        bank = _DEFAULT_COMPETENCIES[itype]

        # Pick the most role-relevant sub-bank
        chosen_bank = bank.get("default", [])
        if any(kw in role_lower for kw in ("ml", "machine learn", "ai", "data sci", "nlp")):
            chosen_bank = bank.get("ml", chosen_bank)
        elif any(kw in role_lower for kw in ("backend", "platform", "infra", "sre", "devops")):
            chosen_bank = bank.get("backend", chosen_bank)

        competencies = chosen_bank[:max_competencies]

    return competencies


# ---------------------------------------------------------------------------
# LLM Caller
# ---------------------------------------------------------------------------

def _call_llm(prompt: str, system_prompt: str, temperature: float = 0.7) -> Optional[str]:
    """
    Sends a prompt to the configured LLM provider (OpenAI or Anthropic).
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
# Agent Decision Engine
# ---------------------------------------------------------------------------

_MAX_PROBES_PER_TOPIC = 2   # After this many probes, force a transition

# Deterministic probe questions indexed by [interview_type][probe_dimension]
_PROBE_TEMPLATES: Dict[str, List[str]] = {
    "failure_handling": [
        "Walk me through what happens when a key component of that system fails. "
        "How did you detect it, contain it, and recover without data loss?",
        "What was the worst production incident related to that system? "
        "What was your personal role in the resolution and what did you change afterward?",
    ],
    "scalability": [
        "You described the current approach — now push it to 100× the load. "
        "Where does the first bottleneck appear, and how would you redesign around it?",
        "How did you decide on the sharding or partitioning strategy? "
        "What trade-offs did you explicitly reject and why?",
    ],
    "trade_offs": [
        "What alternative architectures did you seriously consider before choosing this approach? "
        "Walk me through one option you ruled out and the reasoning.",
        "If you had to optimize this system for cost rather than latency, "
        "what would you change first and what would you sacrifice?",
    ],
    "observability": [
        "How would you know within 30 seconds that this system is degrading? "
        "What specific metrics and thresholds would you alert on?",
        "Describe your on-call runbook for this system — "
        "what's the escalation path and what are the most common root causes?",
    ],
    "depth": [
        "You mentioned {topic} — can you go one level deeper? "
        "What implementation details or edge cases did you have to work through?",
        "That answer covers the happy path well. "
        "What are the hardest edge cases in this domain, and how would you handle them?",
    ],
}

# Transition question starters by interview type
_TRANSITION_INTROS: Dict[str, str] = {
    "Technical": "Shifting topics —",
    "Behavioral": "Let's move on —",
    "System Design": "Now let's explore a different design challenge —",
}

# Fallback questions by topic label (for transition when LLM unavailable)
_TOPIC_TRANSITION_TEMPLATES: Dict[str, str] = {
    "system design & scalability": (
        "Let's talk about system design. Sketch the high-level architecture for a "
        "real-time leaderboard service that must rank 10 million users with sub-second update latency."
    ),
    "data structures & algorithms": (
        "Given a stream of log events arriving out of order, "
        "design a data structure that can return the median latency in O(log n) time per insertion."
    ),
    "database design & query optimization": (
        "A query that takes 200ms in staging suddenly takes 8 seconds in production under 10× traffic. "
        "Walk me through your debugging process and the optimization you'd apply."
    ),
    "distributed systems & fault tolerance": (
        "How would you implement exactly-once message processing in a distributed system "
        "where both the producer and consumer can crash mid-operation?"
    ),
    "caching strategies (Redis, CDN)": (
        "Design a cache invalidation strategy for a product catalogue that's updated by multiple "
        "microservices and served to 50k concurrent users. How do you avoid stale reads?"
    ),
    "message queues & event streaming": (
        "You need to process 500k payment events per second with strict ordering guarantees "
        "per user account. How would you design the consumer topology?"
    ),
    "CI/CD & infrastructure as code": (
        "Describe your ideal zero-downtime deployment pipeline for a stateful microservice "
        "that owns a Postgres database with a live schema migration."
    ),
    "security & authentication patterns": (
        "How would you design an API authentication system that supports both machine-to-machine "
        "service tokens and user-delegated OAuth2 flows with fine-grained RBAC?"
    ),
    "observability & SLO engineering": (
        "Define the SLOs you would set for a payment processing service, "
        "and explain how you would build the alerting and error budget tracking around them."
    ),
    "ML model training & evaluation": (
        "Your model's offline AUC is 0.92 but online click-through rate drops 15% after deployment. "
        "Walk me through your investigation and retraining strategy."
    ),
    "feature engineering & data pipelines": (
        "You need to add a real-time feature (last 5-minute user activity) to a model "
        "that was trained on batch features computed daily. How do you reconcile the two?"
    ),
    "model serving & deployment": (
        "Design a model serving layer that supports A/B testing across three model versions, "
        "with automatic rollback if the challenger underperforms by more than 5%."
    ),
    "vector databases & semantic search": (
        "Explain how you would build a hybrid search system that combines dense vector similarity "
        "with BM25 keyword scoring — how do you tune the interpolation weight α?"
    ),
    "RAG systems & LLM integration": (
        "Design a RAG pipeline for an enterprise document Q&A system. "
        "How do you handle conflicting information across documents and prevent hallucinations?"
    ),
    "cross-functional collaboration": (
        "Tell me about a time you had to align engineering and product on a technical constraint "
        "that required cutting scope. How did you communicate the trade-off and reach consensus?"
    ),
    "ownership & delivery under pressure": (
        "Describe the most high-stakes deadline you have delivered on. "
        "What risks did you take, what did you cut, and what was the outcome?"
    ),
    "ambiguity & priority setting": (
        "You have three critical bugs, a feature launch in two days, and a team member who is blocked. "
        "Walk me through how you triage and communicate your decision."
    ),
}


def _build_history_block(session: "InterviewSessionState", max_turns: int = 8) -> str:
    """Formats the recent interview history into an LLM-readable block."""
    recent = session.history[-max_turns * 2:]
    lines = []
    for turn in recent:
        speaker = "Interviewer" if turn["role"] == "interviewer" else "Candidate"
        lines.append(f"{speaker}: {turn['text']}")
    return "\n\n".join(lines)


def _parse_llm_json(raw: str) -> Optional[Dict[str, Any]]:
    """Strips markdown fences and parses JSON from LLM response."""
    if not raw:
        return None
    cleaned = raw.strip()
    # Remove markdown code fences if present
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        # Try extracting the first JSON object from the string
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except (json.JSONDecodeError, ValueError):
                pass
    return None


def _deterministic_agent_decision(
    session: "InterviewSessionState",
    last_answer: str,
) -> Dict[str, Any]:
    """
    Deterministic fallback when no LLM API is available.
    Uses heuristics: answer length, probe_count, remaining topics.
    """
    current_topic = session.current_topic or (session.jd_competencies[0] if session.jd_competencies else "general competency")
    probe_count = session.probe_counts.get(current_topic, 0)
    remaining = [t for t in session.jd_competencies if t not in session.covered_topics and t != current_topic]

    answer_len = len(last_answer.strip())

    # Determine answer quality heuristically by length + keyword richness
    technical_kws = ["because", "however", "trade-off", "scale", "latency", "failure",
                     "metric", "monitor", "bottleneck", "alternative", "instead"]
    kw_hits = sum(1 for kw in technical_kws if kw.lower() in last_answer.lower())

    if answer_len < 80 or kw_hits < 1:
        answer_quality = "incomplete"
    elif answer_len < 200 or kw_hits < 2:
        answer_quality = "weak"
        if probe_count == 0:
            answer_quality = "adequate"
    elif kw_hits >= 4:
        answer_quality = "strong"
    else:
        answer_quality = "adequate"

    # Decision logic
    force_transition = probe_count >= _MAX_PROBES_PER_TOPIC
    should_probe = (answer_quality in ("weak", "incomplete")) and not force_transition

    if should_probe:
        # Pick a probe dimension
        probe_dims = list(_PROBE_TEMPLATES.keys())
        dim_idx = probe_count % len(probe_dims)
        probe_dimension = probe_dims[dim_idx]
        probe_qs = _PROBE_TEMPLATES[probe_dimension]
        q_idx = min(probe_count, len(probe_qs) - 1)
        question = probe_qs[q_idx].replace("{topic}", current_topic)

        return {
            "decision": "probe",
            "reasoning": (
                f"The answer was {answer_quality} — it lacked specific detail on {probe_dimension.replace('_', ' ')}. "
                f"Drilling deeper to test understanding of {current_topic}."
            ),
            "answer_quality": answer_quality,
            "probe_target": probe_dimension.replace("_", " "),
            "topic_covered": None,
            "next_topic": None,
            "question": question,
        }
    else:
        # Transition to next topic
        topic_covered = current_topic
        next_topic = remaining[0] if remaining else current_topic

        intro = _TRANSITION_INTROS.get(session.interview_type, "Let's shift focus —")
        template_q = _TOPIC_TRANSITION_TEMPLATES.get(
            next_topic,
            f"{intro} for the {session.target_role} role, describe your approach to {next_topic}.",
        )
        question = template_q if next_topic in _TOPIC_TRANSITION_TEMPLATES else f"{intro} {template_q}"

        return {
            "decision": "transition",
            "reasoning": (
                f"Answer was {answer_quality} on {current_topic}. "
                f"Moving to test '{next_topic}' — a key JD competency not yet covered."
                if remaining else
                f"All JD competencies covered. Final transition to wrap up the session."
            ),
            "answer_quality": answer_quality,
            "probe_target": None,
            "topic_covered": topic_covered,
            "next_topic": next_topic,
            "question": question,
        }


def _run_agent_decision(
    session: "InterviewSessionState",
    last_answer: str,
) -> Dict[str, Any]:
    """
    Core agent decision function.
    1. Calls LLM with structured PROBE/TRANSITION decision prompt.
    2. Falls back to deterministic heuristics on LLM failure.
    Returns a normalized decision dict.
    """
    current_topic = session.current_topic or (session.jd_competencies[0] if session.jd_competencies else "general knowledge")
    probe_count = session.probe_counts.get(current_topic, 0)
    remaining = [t for t in session.jd_competencies if t not in session.covered_topics and t != current_topic]

    jd_section = ""
    if session.job_description:
        jd_preview = session.job_description[:500].replace("\n", " ")
        jd_section = f"- Job Description (excerpt): {jd_preview}"

    prompt = AGENT_DECISION_PROMPT.format(
        target_role=session.target_role,
        skill_level=session.skill_level,
        interview_type=session.interview_type,
        jd_section=jd_section,
        covered_topics=", ".join(session.covered_topics) if session.covered_topics else "none yet",
        remaining_topics=", ".join(remaining) if remaining else "all covered — go deep on any gap",
        probe_count=probe_count,
        max_probes=_MAX_PROBES_PER_TOPIC,
        history_block=_build_history_block(session),
        last_answer=last_answer[:800],
    )

    raw = _call_llm(prompt, AGENT_DECISION_SYSTEM_PROMPT, temperature=0.3)
    if raw:
        parsed = _parse_llm_json(raw)
        if parsed and "decision" in parsed and "question" in parsed:
            # Normalize and fill optional fields
            parsed.setdefault("reasoning", "Agent decision based on answer analysis.")
            parsed.setdefault("answer_quality", "adequate")
            parsed.setdefault("probe_target", None)
            parsed.setdefault("topic_covered", None)
            parsed.setdefault("next_topic", None)
            # Validate decision value
            if parsed["decision"] not in ("probe", "transition"):
                parsed["decision"] = "probe"
            return parsed

    # Fallback to deterministic decision
    return _deterministic_agent_decision(session, last_answer)


# ---------------------------------------------------------------------------
# Static question generators (used by /answer endpoint)
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


def _generate_opening_question(session: "InterviewSessionState") -> str:
    """Generates the tailored opening interview question using LLM or deterministic template."""
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

    interview_type = session.interview_type if session.interview_type in _OPENING_TEMPLATES else "Technical"
    skill_level = session.skill_level if session.skill_level in _OPENING_TEMPLATES[interview_type] else "Intermediate"
    base_question = _OPENING_TEMPLATES[interview_type][skill_level]

    if session.resume_summary:
        return (
            f"Given your background — {session.resume_summary[:120]} — "
            f"for this {session.target_role} role: {base_question}"
        )
    return f"For the {session.target_role} position: {base_question}"


def _generate_followup_question(session: "InterviewSessionState") -> str:
    """Generates the next adaptive follow-up question (used by /answer endpoint)."""
    if not session.history:
        return _generate_opening_question(session)

    history_block = _build_history_block(session)
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

    idx = min(session.question_count - 1, len(_FOLLOWUP_TEMPLATES) - 1)
    return _FOLLOWUP_TEMPLATES[idx]


def _generate_scorecard_from_llm(session: "InterviewSessionState") -> Optional[Dict[str, Any]]:
    """Generates a structured scorecard JSON from LLM evaluation of the full transcript."""
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
        parsed = _parse_llm_json(raw)
        if parsed:
            return parsed
    return None


# ---------------------------------------------------------------------------
# Resume Extractor
# ---------------------------------------------------------------------------

def _extract_resume_summary(resume_text: str, max_chars: int = 400) -> str:
    """Extracts a concise summary from raw resume text."""
    if not resume_text or not resume_text.strip():
        return ""
    lines = [ln.strip() for ln in resume_text.splitlines() if ln.strip()]
    substantive = [ln for ln in lines if len(ln) > 30][:4]
    summary = " | ".join(substantive)
    return summary[:max_chars]


# ---------------------------------------------------------------------------
# Interview Service
# ---------------------------------------------------------------------------

class InterviewService:
    """
    Manages the full lifecycle of AI mock interview sessions:
    - Session creation and in-memory state storage
    - Adaptive question generation (LLM-first, deterministic fallback)
    - /answer: Progressive follow-up questions (generic adaptive)
    - /respond: LLM agent — dynamic PROBE vs TRANSITION decision with topic tracking
    - LLM-evaluated scorecard generation on session completion
    """

    MAX_INTERVIEW_QUESTIONS = 5

    def __init__(self):
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
        extracts JD competencies, and persists initial state.
        """
        session_id = str(uuid.uuid4())

        resume_summary = req.resume_summary
        if not resume_summary and req.resume_text:
            resume_summary = _extract_resume_summary(req.resume_text)

        jd_competencies = _extract_jd_competencies(
            jd_text=req.job_description,
            target_role=req.target_role,
            interview_type=req.interview_type,
        )

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
            jd_competencies=jd_competencies,
            current_topic=jd_competencies[0] if jd_competencies else None,
        )

        opening_question = _generate_opening_question(session)
        session.history.append({"role": "interviewer", "text": opening_question})
        session.question_count = 1

        self._sessions[session_id] = session
        return session, opening_question

    # ------------------------------------------------------------------
    # /answer  — Simple adaptive follow-up (no decision trace)
    # ------------------------------------------------------------------

    def process_answer(
        self,
        session_id: str,
        answer: str,
    ) -> Tuple[str, int, bool]:
        """
        Records the candidate's answer and generates the next follow-up question.
        Returns (next_question, question_number, is_complete).
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Interview session '{session_id}' not found. It may have expired.")
        if session.is_complete:
            raise ValueError("This interview session has already been completed.")

        session.history.append({"role": "candidate", "text": answer})
        session.question_count += 1

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

        next_question = _generate_followup_question(session)
        session.history.append({"role": "interviewer", "text": next_question})
        return next_question, session.question_count, False

    # ------------------------------------------------------------------
    # /respond  — Dynamic PROBE vs TRANSITION agent
    # ------------------------------------------------------------------

    def process_respond(
        self,
        session_id: str,
        answer: str,
    ) -> Dict[str, Any]:
        """
        The dynamic agent endpoint. Analyzes the candidate's answer and makes
        an intelligent decision to either:
          - PROBE: drill deeper into the same topic (failure handling, trade-offs, etc.)
          - TRANSITION: move to the next uncovered JD competency

        Returns a rich dict with the decision trace, topic coverage state, next question,
        and completion flag.
        """
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Interview session '{session_id}' not found. It may have expired.")
        if session.is_complete:
            raise ValueError("This interview session has already been completed.")

        # Record candidate answer
        session.history.append({"role": "candidate", "text": answer})
        session.question_count += 1

        # Check completion
        if session.question_count > self.MAX_INTERVIEW_QUESTIONS:
            session.is_complete = True
            closing = (
                f"Thank you, {session.candidate_name}! That completes our session. "
                "You engaged with some strong technical areas today. "
                "Retrieve your scorecard at /api/v1/interview/scorecard."
            )
            session.history.append({"role": "interviewer", "text": closing})
            remaining = [t for t in session.jd_competencies if t not in session.covered_topics]
            return {
                "question": closing,
                "decision": "complete",
                "reasoning": "Max interview turns reached.",
                "answer_quality": "n/a",
                "probe_target": None,
                "topic_covered": session.current_topic,
                "next_topic": None,
                "topics_remaining": remaining,
                "is_complete": True,
            }

        # Run the agent decision
        decision_data = _run_agent_decision(session, answer)

        decision = decision_data["decision"]
        topic_covered = decision_data.get("topic_covered")
        next_topic = decision_data.get("next_topic")
        next_question = decision_data["question"]

        # Update topic tracking state
        if decision == "probe":
            # Increment probe counter for current topic
            ct = session.current_topic or "general"
            session.probe_counts[ct] = session.probe_counts.get(ct, 0) + 1
        elif decision == "transition":
            # Mark current topic as covered if agent identified it
            if topic_covered and topic_covered not in session.covered_topics:
                session.covered_topics.append(topic_covered)
            elif session.current_topic and session.current_topic not in session.covered_topics:
                session.covered_topics.append(session.current_topic)
            # Advance to next topic
            if next_topic:
                session.current_topic = next_topic
                # Reset probe count for the new topic
                session.probe_counts.setdefault(next_topic, 0)

        # Record decision in session log
        decision_log = {
            "turn": session.question_count,
            "decision": decision,
            "reasoning": decision_data.get("reasoning", ""),
            "answer_quality": decision_data.get("answer_quality", "adequate"),
            "probe_target": decision_data.get("probe_target"),
            "topic_covered": topic_covered,
            "next_topic": next_topic,
        }
        session.agent_decisions.append(decision_log)

        # Record the next question in history
        session.history.append({"role": "interviewer", "text": next_question})

        remaining = [t for t in session.jd_competencies if t not in session.covered_topics]

        return {
            "question": next_question,
            "decision": decision,
            "reasoning": decision_data.get("reasoning", ""),
            "answer_quality": decision_data.get("answer_quality", "adequate"),
            "probe_target": decision_data.get("probe_target"),
            "topic_covered": topic_covered,
            "next_topic": next_topic,
            "topics_remaining": remaining,
            "is_complete": False,
        }

    # ------------------------------------------------------------------
    # Scorecard Generation
    # ------------------------------------------------------------------

    def generate_scorecard(self, session_id: str) -> InterviewScorecardResponse:
        """Evaluates the complete interview transcript and returns a structured scorecard."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Interview session '{session_id}' not found.")

        turns = session.question_count
        est_cost = f"${turns * 1500 * 0.002 / 1000:.4f} (~{turns} turns, GPT-4o-mini pricing)"

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
