import uuid
from typing import Dict, Any, List, Tuple
from app.models.schemas import InterviewInitRequest, InterviewScorecardResponse

class InterviewSession:
    def __init__(self, init_req: InterviewInitRequest):
        self.session_id = str(uuid.uuid4())
        self.candidate_name = init_req.candidate_name
        self.target_role = init_req.target_role
        self.skill_level = init_req.skill_level
        self.interview_type = init_req.interview_type
        self.resume_summary = init_req.resume_summary
        self.history: List[Dict[str, str]] = []
        self.question_count = 0

class InterviewService:
    def __init__(self):
        self.sessions: Dict[str, InterviewSession] = {}

    def create_session(self, init_req: InterviewInitRequest) -> Tuple[str, str]:
        session = InterviewSession(init_req)
        self.sessions[session.session_id] = session
        
        # Initial adaptive question based on role & skill
        first_q = f"Hello {session.candidate_name}! Let's start the {session.interview_type} interview for the {session.target_role} role. Could you briefly introduce a recent project you worked on and the key architecture decisions you made?"
        session.history.append({"role": "interviewer", "text": first_q})
        session.question_count = 1
        return session.session_id, first_q

    def process_candidate_answer(self, session_id: str, answer: str) -> Tuple[str, int, bool]:
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError("Session not found")
        
        session.history.append({"role": "candidate", "text": answer})
        session.question_count += 1
        
        if session.question_count > 4:
            return "Thank you! We have covered all the key areas. Generating your interview scorecard now...", session.question_count, True
            
        # Dynamic follow-up generation
        next_q = f"That's interesting regarding '{answer[:40]}...'. Can you elaborate on how you handled edge cases, performance trade-offs, or scalability in that approach?"
        session.history.append({"role": "interviewer", "text": next_q})
        return next_q, session.question_count, False

    def generate_scorecard(self, session_id: str) -> InterviewScorecardResponse:
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError("Session not found")
            
        return InterviewScorecardResponse(
            session_id=session_id,
            overall_score=86.5,
            technical_knowledge_score=88.0,
            communication_score=85.0,
            problem_solving_score=87.0,
            answer_structure_score=86.0,
            strengths=[
                "Clear explanation of technical design choices and trade-offs.",
                "Good understanding of timestamp-aware indexing and vector search constraints."
            ],
            improvement_areas=[
                "Could elaborate more on cost optimization under high concurrent load.",
                "Provide deeper details on fallback mechanisms when document retrieval yields low confidence."
            ],
            recommendations=[
                "Review AWS Bedrock pricing models for multi-tenant deployments.",
                "Practice STAR format for behavioral and system design follow-ups."
            ],
            estimated_operating_cost="$0.04 (15-min interactive session with 4 turns)"
        )

interview_service = InterviewService()
