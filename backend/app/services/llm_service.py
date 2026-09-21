import time
from typing import List, Dict, Any, Tuple
from app.models.schemas import SourceCitation

class LLMService:
    def format_timestamp(self, seconds: float) -> str:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    def generate_grounded_answer(
        self,
        question: str,
        retrieved_contexts: List[Dict[str, Any]],
        current_timestamp: float
    ) -> Tuple[str, List[SourceCitation], bool, float]:
        start_time = time.time()
        
        timestamp_str = f"00:00 - {self.format_timestamp(current_timestamp)}"

        if not retrieved_contexts:
            latency = (time.time() - start_time) * 1000
            return (
                f"I'm sorry, but based on the video content watched up to {self.format_timestamp(current_timestamp)} and available permitted resources, I could not find information to answer your question.",
                [],
                True,
                latency
            )

        citations = []
        context_snippets = []

        for ctx in retrieved_contexts:
            if ctx["type"] == "video":
                t_start = self.format_timestamp(ctx["start_time"])
                t_end = self.format_timestamp(ctx["end_time"])
                citation = SourceCitation(
                    source_type="video",
                    resource_id=ctx["resource_id"],
                    title=ctx["resource_title"],
                    timestamp_start=ctx["start_time"],
                    timestamp_end=ctx["end_time"],
                    snippet=ctx["content"][:120] + "..."
                )
                citations.append(citation)
                context_snippets.append(f"[Video {t_start}-{t_end}]: {ctx['content']}")
            else:
                citation = SourceCitation(
                    source_type=ctx["type"],
                    resource_id=ctx["resource_id"],
                    title=ctx["resource_title"],
                    page_number=ctx["page_number"],
                    snippet=ctx["content"][:120] + "..."
                )
                citations.append(citation)
                context_snippets.append(f"[{ctx['type'].upper()} Page/Slide {ctx['page_number']}]: {ctx['content']}")

        # Simulated grounded LLM synthesis (pluggable with AWS Bedrock / OpenAI)
        answer_text = (
            f"Based on the lecture up to {self.format_timestamp(current_timestamp)} and supporting materials, "
            f"here is the explanation: {retrieved_contexts[0]['content']} "
            f"This is supported by the instructor's discussion at {self.format_timestamp(retrieved_contexts[0].get('start_time', 0))}."
        )

        latency = (time.time() - start_time) * 1000
        return answer_text, citations, False, latency

llm_service = LLMService()
