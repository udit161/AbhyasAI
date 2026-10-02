import os
import sys
import time
import json
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple

# Ensure backend directory is in python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.db.vector_store import vector_store
from app.services.retrieval_service import retrieval_service
from app.services.llm_service import llm_service


@dataclass
class TestCase:
    id: str
    category: str  # 'past_timestamp', 'future_timestamp', 'out_of_bounds', 'follow_up'
    description: str
    video_id: str
    current_timestamp: float
    question: str
    conversation_history: Optional[List[Dict[str, str]]] = field(default_factory=list)
    allowed_resource_ids: Optional[List[str]] = field(default_factory=list)
    expected_refusal: bool = False
    expected_keywords: List[str] = field(default_factory=list)
    forbidden_keywords: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Pre-defined Evaluation Dataset covering required test categories
# ---------------------------------------------------------------------------
EVALUATION_DATASET: List[TestCase] = [
    # 1. Past Timestamps: Questions about content presented BEFORE current timestamp
    TestCase(
        id="TC-PAST-01",
        category="past_timestamp",
        description="Question about RAG architecture discussed in watched segment (0-600s)",
        video_id="test_vid_timestamp_check",
        current_timestamp=600.0,
        question="What is the overview of RAG architecture fundamentals?",
        allowed_resource_ids=["test_vid_timestamp_check"],
        expected_refusal=False,
        expected_keywords=["RAG", "architecture", "fundamentals"],
    ),
    TestCase(
        id="TC-PAST-02",
        category="past_timestamp",
        description="Question about timestamp filtering discussed at 600-1120s mark when user is at 1120s",
        video_id="test_vid_timestamp_check",
        current_timestamp=1120.0,
        question="How does timestamp filtering work in the vector store?",
        allowed_resource_ids=["test_vid_timestamp_check"],
        expected_refusal=False,
        expected_keywords=["timestamp", "filtering", "vector"],
    ),
    TestCase(
        id="TC-PAST-03",
        category="past_timestamp",
        description="Question about watched video content and allowed supporting PDF cheatsheet",
        video_id="test_vid_with_doc",
        current_timestamp=300.0,
        question="What query optimization techniques are mentioned in the cheatsheet?",
        allowed_resource_ids=["test_vid_with_doc", "test_pdf_cheatsheet"],
        expected_refusal=False,
        expected_keywords=["optimization", "cheatsheet"],
    ),

    # 2. Future Timestamp Filtering: Questions about content discussed LATER in lecture
    TestCase(
        id="TC-PAST-FUTURE-01",
        category="future_timestamp",
        description="Question about Graph Neural Networks discussed at 1122s+ when user is only at 300s",
        video_id="test_vid_timestamp_check",
        current_timestamp=300.0,
        question="What are graph neural networks and future topic spoilers?",
        allowed_resource_ids=["test_vid_timestamp_check"],
        expected_refusal=True,
        forbidden_keywords=["graph neural networks", "spoiler"],
    ),
    TestCase(
        id="TC-PAST-FUTURE-02",
        category="future_timestamp",
        description="Question about advanced future topic when user is at 600s",
        video_id="test_vid_timestamp_check",
        current_timestamp=600.0,
        question="Can you explain graph neural networks covered later in the video?",
        allowed_resource_ids=["test_vid_timestamp_check"],
        expected_refusal=True,
        forbidden_keywords=["graph neural networks"],
    ),

    # 3. Out-of-Bounds Questions: Questions completely outside the video context
    TestCase(
        id="TC-OOB-01",
        category="out_of_bounds",
        description="Question about general astrophysics / space trivia outside domain",
        video_id="test_vid_timestamp_check",
        current_timestamp=1000.0,
        question="What is the capital city of Mars and its population density?",
        allowed_resource_ids=["test_vid_timestamp_check"],
        expected_refusal=True,
    ),
    TestCase(
        id="TC-OOB-02",
        category="out_of_bounds",
        description="Question about cooking recipes unrelated to AI engineering",
        video_id="test_vid_timestamp_check",
        current_timestamp=1000.0,
        question="How do you bake a traditional Italian margherita pizza?",
        allowed_resource_ids=["test_vid_timestamp_check"],
        expected_refusal=True,
    ),
    TestCase(
        id="TC-OOB-03",
        category="out_of_bounds",
        description="Question about quantum mechanics superposition",
        video_id="test_main_vid_1",
        current_timestamp=100.0,
        question="How do qubits achieve quantum entanglement and superposition?",
        allowed_resource_ids=["test_main_vid_1"],
        expected_refusal=True,
    ),

    # 4. Follow-up Questions: Multi-turn chat questions referencing context
    TestCase(
        id="TC-FOLLOWUP-01",
        category="follow_up",
        description="Follow-up question building on previous explanation of FastAPI",
        video_id="test_main_vid_1",
        current_timestamp=100.0,
        question="How does it handle data validation with Pydantic?",
        conversation_history=[
            {"role": "user", "content": "What web framework is discussed?"},
            {"role": "assistant", "content": "The lecture discusses FastAPI for web applications."}
        ],
        allowed_resource_ids=["test_main_vid_1"],
        expected_refusal=False,
        expected_keywords=["Pydantic", "validation"],
    ),
    TestCase(
        id="TC-FOLLOWUP-02",
        category="follow_up",
        description="Follow-up question asking for specific details from sliding window discussion",
        video_id="test_vid_pipeline_999",
        current_timestamp=140.0,
        question="What metadata does each window preserve during chunking?",
        conversation_history=[
            {"role": "user", "content": "What is sliding window chunking?"},
            {"role": "assistant", "content": "Sliding window chunking groups transcript timestamps into continuous contexts."}
        ],
        allowed_resource_ids=["test_vid_pipeline_999"],
        expected_refusal=False,
        expected_keywords=["start time", "end time", "metadata"],
    ),
]


from app.models.vector_schema import VectorDocument, VectorMetadata, ResourceType


def seed_evaluation_data():
    """
    Ensures test documents and timestamped video segments are seeded into vector store.
    """
    sample_docs = [
        VectorDocument(
            id="vid_test_vid_timestamp_check_seg_0",
            content="Segment 1: Overview of RAG architecture fundamentals.",
            metadata=VectorMetadata(
                resource_id="test_vid_timestamp_check",
                course_id=None,
                resource_type=ResourceType.VIDEO,
                title="Lecture on RAG System Design",
                text_chunk="Segment 1: Overview of RAG architecture fundamentals.",
                start_time=0.0,
                end_time=600.0,
                page_number=None,
                slide_index=None,
                chunk_index=0
            )
        ),
        VectorDocument(
            id="vid_test_vid_timestamp_check_seg_1",
            content="Segment 2: Timestamp filtering and boundary enforcement in vector store.",
            metadata=VectorMetadata(
                resource_id="test_vid_timestamp_check",
                course_id=None,
                resource_type=ResourceType.VIDEO,
                title="Lecture on RAG System Design",
                text_chunk="Segment 2: Timestamp filtering and boundary enforcement in vector store.",
                start_time=600.0,
                end_time=1120.0,
                page_number=None,
                slide_index=None,
                chunk_index=1
            )
        ),
        VectorDocument(
            id="vid_test_vid_timestamp_check_seg_2",
            content="Segment 3: Advanced future topic spoiler about graph neural networks.",
            metadata=VectorMetadata(
                resource_id="test_vid_timestamp_check",
                course_id=None,
                resource_type=ResourceType.VIDEO,
                title="Lecture on RAG System Design",
                text_chunk="Segment 3: Advanced future topic spoiler about graph neural networks.",
                start_time=1122.0,
                end_time=1800.0,
                page_number=None,
                slide_index=None,
                chunk_index=2
            )
        ),
        VectorDocument(
            id="vid_test_main_vid_1_seg_0",
            content="FastAPI uses Pydantic models for data validation and OpenAPI schema generation.",
            metadata=VectorMetadata(
                resource_id="test_main_vid_1",
                course_id=None,
                resource_type=ResourceType.VIDEO,
                title="FastAPI RAG Course",
                text_chunk="FastAPI uses Pydantic models for data validation and OpenAPI schema generation.",
                start_time=0.0,
                end_time=100.0,
                page_number=None,
                slide_index=None,
                chunk_index=0
            )
        ),
        VectorDocument(
            id="vid_test_vid_pipeline_999_seg_0",
            content="Welcome to the Fullstack AI Engineering course. In this lecture, we explore retrieval augmented generation. RAG enables LLMs to access domain knowledge without full fine-tuning by searching vector database stores. When processing video transcripts, grouping timestamps into sliding windows maintains continuous context. Each window preserves the precise start time and end time metadata for exact playback timestamp grounding.",
            metadata=VectorMetadata(
                resource_id="test_vid_pipeline_999",
                course_id=None,
                resource_type=ResourceType.VIDEO,
                title="Sample RAG Architecture Lecture",
                text_chunk="Welcome to the Fullstack AI Engineering course. In this lecture, we explore retrieval augmented generation. RAG enables LLMs to access domain knowledge without full fine-tuning by searching vector database stores. When processing video transcripts, grouping timestamps into sliding windows maintains continuous context. Each window preserves the precise start time and end time metadata for exact playback timestamp grounding.",
                start_time=0.0,
                end_time=140.0,
                page_number=None,
                slide_index=None,
                chunk_index=0
            )
        ),
        VectorDocument(
            id="pdf_test_pdf_cheatsheet_pg_5",
            content="Supporting CheatSheet: Query optimization techniques.",
            metadata=VectorMetadata(
                resource_id="test_pdf_cheatsheet",
                course_id=None,
                resource_type=ResourceType.PDF,
                title="RAG Systems CheatSheet PDF",
                text_chunk="Supporting CheatSheet: Query optimization techniques.",
                start_time=None,
                end_time=None,
                page_number=5,
                slide_index=None,
                chunk_index=0
            )
        )
    ]

    existing_ids = {d.id for d in vector_store.documents}
    for doc in sample_docs:
        if doc.id not in existing_ids:
            vector_store.documents.append(doc)
    vector_store._save_documents()


class SystemEvaluator:
    """
    Automated evaluation harness for calculating:
    - Retrieval Precision
    - Citation Accuracy
    - Hallucination Rate
    - Timestamp Compliance Rate
    - System Latency
    """

    def __init__(self, dataset: List[TestCase] = EVALUATION_DATASET):
        self.dataset = dataset
        seed_evaluation_data()

    def evaluate_single_case(self, test_case: TestCase) -> Dict[str, Any]:
        """
        Runs retrieval & answer generation for a single test case and evaluates metrics.
        """
        start_time = time.perf_counter()

        # 1. Execute Context Retrieval
        retrieved_contexts = retrieval_service.retrieve_grounded_context(
            query=test_case.question,
            video_id=test_case.video_id,
            current_timestamp=test_case.current_timestamp,
            permitted_doc_ids=test_case.allowed_resource_ids,
            top_k=5,
        )

        # 2. Execute LLM Answer Generation
        answer_text, citations, is_refusal, latency_ms = llm_service.generate_grounded_answer(
            question=test_case.question,
            retrieved_contexts=retrieved_contexts,
            current_timestamp=test_case.current_timestamp,
            conversation_history=test_case.conversation_history,
        )

        exec_latency = (time.perf_counter() - start_time) * 1000.0

        # 3. Calculate Retrieval Precision
        retrieval_precision, timestamp_compliant_count = self._calc_retrieval_precision(
            retrieved_contexts=retrieved_contexts,
            max_timestamp=test_case.current_timestamp,
            expected_refusal=test_case.expected_refusal,
            allowed_resource_ids=test_case.allowed_resource_ids,
        )

        # 4. Calculate Citation Accuracy
        citation_accuracy = self._calc_citation_accuracy(
            citations=citations,
            retrieved_contexts=retrieved_contexts,
            is_refusal=is_refusal,
            expected_refusal=test_case.expected_refusal,
        )

        # 5. Calculate Hallucination Status
        is_hallucinated, hallucination_reason = self._detect_hallucination(
            test_case=test_case,
            answer_text=answer_text,
            citations=citations,
            retrieved_contexts=retrieved_contexts,
            is_refusal=is_refusal,
        )

        # Refusal Compliance Check
        refusal_correct = (is_refusal == test_case.expected_refusal)

        return {
            "test_id": test_case.id,
            "category": test_case.category,
            "description": test_case.description,
            "question": test_case.question,
            "current_timestamp": test_case.current_timestamp,
            "num_retrieved": len(retrieved_contexts),
            "retrieval_precision": round(retrieval_precision, 4),
            "timestamp_compliant_count": timestamp_compliant_count,
            "citation_count": len(citations),
            "citation_accuracy": round(citation_accuracy, 4),
            "is_refusal": is_refusal,
            "expected_refusal": test_case.expected_refusal,
            "refusal_correct": refusal_correct,
            "is_hallucinated": is_hallucinated,
            "hallucination_reason": hallucination_reason,
            "answer_snippet": answer_text[:120] + "..." if len(answer_text) > 120 else answer_text,
            "latency_ms": round(exec_latency, 2),
        }

    def _calc_retrieval_precision(
        self,
        retrieved_contexts: List[Dict[str, Any]],
        max_timestamp: float,
        expected_refusal: bool,
        allowed_resource_ids: Optional[List[str]],
    ) -> Tuple[float, int]:
        """
        Retrieval Precision = (Valid Context Chunks Retrieved) / (Total Context Chunks Retrieved)
        A context chunk is valid if:
        1) For video chunks, end_time <= max_timestamp
        2) Resource ID is within allowed_resource_ids (or video_id)
        """
        if not retrieved_contexts:
            # If expected refusal (no relevant past context), precision is 1.0 (0 noise).
            # If answer expected but 0 retrieved, precision is 0.0.
            return (1.0 if expected_refusal else 0.0), 0

        valid_count = 0
        timestamp_compliant_count = 0

        for ctx in retrieved_contexts:
            is_valid = True
            source_type = ctx.get("source_type", "video")
            end_t = ctx.get("end_time")

            # Check timestamp upper bound rule for videos
            if source_type == "video" and end_t is not None:
                if end_t <= max_timestamp:
                    timestamp_compliant_count += 1
                else:
                    is_valid = False

            # Check permitted resource ID rule
            if allowed_resource_ids:
                res_id = ctx.get("resource_id")
                if res_id and res_id not in allowed_resource_ids:
                    is_valid = False

            if is_valid:
                valid_count += 1

        precision = valid_count / len(retrieved_contexts)
        return precision, timestamp_compliant_count

    def _calc_citation_accuracy(
        self,
        citations: List[Any],
        retrieved_contexts: List[Dict[str, Any]],
        is_refusal: bool,
        expected_refusal: bool,
    ) -> float:
        """
        Citation Accuracy = (Citations matching retrieved context) / (Total Citations)
        - If system correctly refuses and outputs 0 citations, accuracy is 1.0 (100%).
        - If system generates citations for non-existent/unretrieved contexts, accuracy drops.
        """
        if is_refusal or expected_refusal:
            return 1.0 if len(citations) == 0 else 0.0

        if not citations:
            return 0.0 if retrieved_contexts else 1.0

        retrieved_res_ids = {c.get("resource_id") for c in retrieved_contexts}
        retrieved_texts = " ".join([c.get("snippet", "").lower() for c in retrieved_contexts])

        accurate_citations = 0
        for cite in citations:
            # Handle Pydantic model or dict representation
            res_id = getattr(cite, "resource_id", None) or cite.get("resource_id")
            snippet = getattr(cite, "snippet", None) or cite.get("snippet", "")

            # Verify resource ID exists in retrieved context
            res_match = res_id in retrieved_res_ids
            # Verify snippet overlap with retrieved text
            snippet_words = [w for w in snippet.lower().split() if len(w) > 3]
            text_match = any(word in retrieved_texts for word in snippet_words[:5]) if snippet_words else True

            if res_match and text_match:
                accurate_citations += 1

        return accurate_citations / len(citations)

    def _detect_hallucination(
        self,
        test_case: TestCase,
        answer_text: str,
        citations: List[Any],
        retrieved_contexts: List[Dict[str, Any]],
        is_refusal: bool,
    ) -> Tuple[bool, Optional[str]]:
        """
        Identifies whether answer contains a hallucination:
        1) Refusal Failure: Model answered an out-of-bounds or future query instead of refusing.
        2) Forbidden Leak: Model revealed forbidden keywords (e.g. future topic spoilers).
        3) Ungrounded Claim: Citations reference non-existent context chunks.
        """
        # 1. Expected refusal but generated answer
        if test_case.expected_refusal and not is_refusal:
            return True, f"Failed to refuse expected out-of-bounds/future query '{test_case.question}'"

        # 2. Check for forbidden keywords (e.g. future content leaks)
        for kw in test_case.forbidden_keywords:
            if kw.lower() in answer_text.lower():
                return True, f"Answer contains forbidden future leak keyword '{kw}'"

        # 3. Check for ungrounded citations
        if not is_refusal and citations:
            retrieved_ids = {c.get("resource_id") for c in retrieved_contexts}
            for cite in citations:
                res_id = getattr(cite, "resource_id", None) or cite.get("resource_id")
                if res_id not in retrieved_ids:
                    return True, f"Citation references unretrieved resource_id '{res_id}'"

        return False, None

    def run_all(self) -> Dict[str, Any]:
        """
        Executes full evaluation suite across all test cases and aggregates statistics.
        """
        print("\n" + "=" * 80)
        print("  AUTOMATED SYSTEM EVALUATION RUNNER")
        print("  Evaluating Retrieval Precision, Citation Accuracy & Hallucination Rates")
        print("=" * 80)

        results = []
        category_stats: Dict[str, Dict[str, Any]] = {}

        for test_case in self.dataset:
            res = self.evaluate_single_case(test_case)
            results.append(res)

            cat = test_case.category
            if cat not in category_stats:
                category_stats[cat] = {
                    "count": 0,
                    "precision_sum": 0.0,
                    "citation_acc_sum": 0.0,
                    "hallucinations": 0,
                    "refusal_correct": 0,
                    "latency_sum": 0.0,
                }

            category_stats[cat]["count"] += 1
            category_stats[cat]["precision_sum"] += res["retrieval_precision"]
            category_stats[cat]["citation_acc_sum"] += res["citation_accuracy"]
            category_stats[cat]["hallucinations"] += 1 if res["is_hallucinated"] else 0
            category_stats[cat]["refusal_correct"] += 1 if res["refusal_correct"] else 0
            category_stats[cat]["latency_sum"] += res["latency_ms"]

        # Aggregate Global Metrics
        total_queries = len(results)
        avg_retrieval_precision = sum(r["retrieval_precision"] for r in results) / total_queries
        avg_citation_accuracy = sum(r["citation_accuracy"] for r in results) / total_queries
        total_hallucinations = sum(1 for r in results if r["is_hallucinated"])
        hallucination_rate = total_hallucinations / total_queries
        refusal_accuracy = sum(1 for r in results if r["refusal_correct"]) / total_queries
        avg_latency = sum(r["latency_ms"] for r in results) / total_queries

        total_retrieved_video_chunks = sum(r["num_retrieved"] for r in results)
        total_timestamp_compliant = sum(r["timestamp_compliant_count"] for r in results)
        timestamp_compliance_rate = (
            (total_timestamp_compliant / total_retrieved_video_chunks)
            if total_retrieved_video_chunks > 0 else 1.0
        )

        summary = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_queries": total_queries,
            "metrics": {
                "retrieval_precision": round(avg_retrieval_precision * 100, 2),
                "citation_accuracy": round(avg_citation_accuracy * 100, 2),
                "hallucination_rate": round(hallucination_rate * 100, 2),
                "timestamp_compliance_rate": round(timestamp_compliance_rate * 100, 2),
                "refusal_accuracy": round(refusal_accuracy * 100, 2),
                "average_latency_ms": round(avg_latency, 2),
            },
            "category_breakdown": {
                cat: {
                    "count": stats["count"],
                    "avg_precision": round((stats["precision_sum"] / stats["count"]) * 100, 2),
                    "avg_citation_accuracy": round((stats["citation_acc_sum"] / stats["count"]) * 100, 2),
                    "hallucination_rate": round((stats["hallucinations"] / stats["count"]) * 100, 2),
                    "refusal_accuracy": round((stats["refusal_correct"] / stats["count"]) * 100, 2),
                    "avg_latency_ms": round(stats["latency_sum"] / stats["count"], 2),
                }
                for cat, stats in category_stats.items()
            },
            "detailed_results": results,
        }

        self._print_summary_table(summary)
        self._save_results(summary)
        return summary

    def _print_summary_table(self, summary: Dict[str, Any]):
        """
        Prints clean formatted results table.
        """
        m = summary["metrics"]
        print("\n" + "-" * 80)
        print("  AGGREGATED EVALUATION SUMMARY METRICS")
        print("-" * 80)
        print(f"  Total Evaluation Queries     : {summary['total_queries']}")
        print(f"  Retrieval Precision          : {m['retrieval_precision']}%")
        print(f"  Citation Accuracy            : {m['citation_accuracy']}%")
        print(f"  Hallucination Rate           : {m['hallucination_rate']}%")
        print(f"  Timestamp Compliance Rate    : {m['timestamp_compliance_rate']}%")
        print(f"  Refusal Compliance Accuracy  : {m['refusal_accuracy']}%")
        print(f"  Average Execution Latency    : {m['average_latency_ms']} ms")
        print("-" * 80)

        print("\n  CATEGORY BREAKDOWN:")
        print(f"  {'Category':<22} | {'Queries':<7} | {'Precision':<10} | {'Citation Acc':<12} | {'Hallucination':<13} | {'Avg Latency':<11}")
        print("  " + "-" * 85)
        for cat, cb in summary["category_breakdown"].items():
            print(f"  {cat:<22} | {cb['count']:<7} | {cb['avg_precision']:>8.1f}% | {cb['avg_citation_accuracy']:>10.1f}% | {cb['hallucination_rate']:>11.1f}% | {cb['avg_latency_ms']:>8.1f} ms")
        print("  " + "-" * 85 + "\n")

    def _save_results(self, summary: Dict[str, Any]):
        """
        Saves structured evaluation results to evaluation/evaluation_results.json
        """
        output_dir = os.path.join(BASE_DIR, "evaluation")
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, "evaluation_results.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"[+] Evaluation results saved successfully to: {filepath}\n")


def run_evaluations():
    evaluator = SystemEvaluator()
    return evaluator.run_all()


if __name__ == "__main__":
    run_evaluations()
