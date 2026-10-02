import time
import os
from typing import List, Dict, Any, Tuple, Optional
from app.core.config import settings
from app.models.schemas import SourceCitation


SYSTEM_PROMPT = """You are an AI Learning Assistant designed to answer questions strictly grounded in the provided lecture video transcripts and supporting course documents.

CRITICAL INSTRUCTIONS:
1. Answer the user query using ONLY the provided context.
2. You must cite your sources explicitly in your text response (e.g., [Video MM:SS-MM:SS], [PDF Page X], [PPT Slide Y]).
3. If the answer cannot be found in the provided context, state that you do not know and refuse to answer rather than hallucinating.
4. Do NOT use outside knowledge or make up facts that are not present in the context.
"""


class LLMService:
    """
    LLM Generation Service providing grounded RAG generation with strict citation enforcement
    and anti-hallucination refusal controls.
    """

    def format_timestamp(self, seconds: Optional[float]) -> str:
        if seconds is None or seconds < 0:
            return "00:00"
        total_sec = int(seconds)
        mins = total_sec // 60
        secs = total_sec % 60
        return f"{mins:02d}:{secs:02d}"

    def build_context_block(self, retrieved_contexts: List[Dict[str, Any]]) -> Tuple[str, List[SourceCitation]]:
        """
        Formats retrieved context chunks into a structured prompt context block with citation tags,
        and constructs Pydantic SourceCitation models.
        """
        citations: List[SourceCitation] = []
        context_snippets: List[str] = []

        for idx, ctx in enumerate(retrieved_contexts):
            source_num = idx + 1
            source_type = ctx.get("source_type", ctx.get("type", "video")).lower()
            res_id = ctx.get("resource_id", "res_unk")
            title = ctx.get("title", ctx.get("resource_title", "Course Resource"))
            content = ctx.get("snippet", ctx.get("content", "")).strip()

            if source_type == "video":
                start_t = ctx.get("start_time", 0.0)
                end_t = ctx.get("end_time", 0.0)
                t_start_str = self.format_timestamp(start_t)
                t_end_str = self.format_timestamp(end_t)
                tag = f"[Source {source_num}: Video {t_start_str}-{t_end_str} | {title}]"

                citation = SourceCitation(
                    source_type="video",
                    resource_id=res_id,
                    title=title,
                    timestamp_start=start_t,
                    timestamp_end=end_t,
                    snippet=content[:150] + ("..." if len(content) > 150 else ""),
                )
            elif source_type == "pdf":
                page_num = ctx.get("page_number", 1)
                tag = f"[Source {source_num}: PDF Page {page_num} | {title}]"

                citation = SourceCitation(
                    source_type="pdf",
                    resource_id=res_id,
                    title=title,
                    page_number=page_num,
                    snippet=content[:150] + ("..." if len(content) > 150 else ""),
                )
            elif source_type == "ppt":
                slide_idx = ctx.get("slide_index", ctx.get("page_number", 1))
                tag = f"[Source {source_num}: PPT Slide {slide_idx} | {title}]"

                citation = SourceCitation(
                    source_type="ppt",
                    resource_id=res_id,
                    title=title,
                    page_number=slide_idx,
                    snippet=content[:150] + ("..." if len(content) > 150 else ""),
                )
            else:
                tag = f"[Source {source_num}: Document | {title}]"
                citation = SourceCitation(
                    source_type="note",
                    resource_id=res_id,
                    title=title,
                    snippet=content[:150] + ("..." if len(content) > 150 else ""),
                )

            citations.append(citation)
            context_snippets.append(f"{tag}\n{content}")

        formatted_context = "\n\n".join(context_snippets)
        return formatted_context, citations

    def generate_grounded_answer(
        self,
        question: str,
        retrieved_contexts: List[Dict[str, Any]],
        current_timestamp: float,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Tuple[str, List[SourceCitation], bool, float]:
        """
        Generates grounded answer strictly citing retrieved context.
        Returns (answer_text, citations, is_refusal, latency_ms).
        """
        start_time = time.time()

        # Check if any contexts were retrieved
        if not retrieved_contexts:
            latency = (time.time() - start_time) * 1000
            timestamp_formatted = self.format_timestamp(current_timestamp)
            return (
                f"I do not know based on the provided context. No relevant information was found in the video transcript watched up to {timestamp_formatted} or permitted supporting documents.",
                [],
                True,  # Refusal flag set
                latency,
            )

        # Build context block and Pydantic citations
        context_block, citations = self.build_context_block(retrieved_contexts)

        # Attempt API call to OpenAI / Bedrock if API keys exist
        api_answer = self._call_llm_api(question, context_block, conversation_history)

        if api_answer:
            answer_text = api_answer
            is_refusal = "do not know" in answer_text.lower() or "cannot be found" in answer_text.lower()
        else:
            # Grounded synthesis fallback using retrieved context and explicit citations
            top_ctx = retrieved_contexts[0]
            top_type = top_ctx.get("source_type", top_ctx.get("type", "video"))
            top_content = top_ctx.get("snippet", top_ctx.get("content", ""))

            if top_type == "video":
                citation_label = f"Video {self.format_timestamp(top_ctx.get('start_time'))}-{self.format_timestamp(top_ctx.get('end_time'))}"
            elif top_type == "pdf":
                citation_label = f"PDF Page {top_ctx.get('page_number', 1)}"
            elif top_type == "ppt":
                citation_label = f"PPT Slide {top_ctx.get('slide_index', 1)}"
            else:
                citation_label = "Supporting Document"

            answer_text = (
                f"Based on the provided context ({citation_label}): {top_content} "
                f"[{citation_label}]"
            )
            is_refusal = False

        latency = (time.time() - start_time) * 1000
        return answer_text, citations, is_refusal, latency

    def _call_llm_api(
        self,
        question: str,
        context_block: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Optional[str]:
        """
        Attempts API generation call to OpenAI or Bedrock if configured.
        """
        if settings.OPENAI_API_KEY:
            try:
                import urllib.request
                import json

                url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                }
                messages = [{"role": "system", "content": SYSTEM_PROMPT}]

                if conversation_history:
                    for msg in conversation_history[-4:]:
                        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

                user_prompt = f"Context Material:\n{context_block}\n\nUser Question: {question}"
                messages.append({"role": "user", "content": user_prompt})

                payload = {
                    "model": settings.OPENAI_MODEL,
                    "messages": messages,
                    "temperature": 0.1,
                }
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(url, data=data, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    return res_json["choices"][0]["message"]["content"]
            except Exception:
                pass

        return None


llm_service = LLMService()
