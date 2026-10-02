import pytest
from app.services.llm_service import llm_service


def test_llm_service_grounded_answer_with_citations():
    """
    Test generating a grounded answer with explicit source citations.
    """
    retrieved_contexts = [
        {
            "source_type": "video",
            "resource_id": "vid_101",
            "title": "Machine Learning Overview",
            "snippet": "Supervised learning uses labeled dataset pairs to train prediction models.",
            "start_time": 60.0,
            "end_time": 180.0,
            "relevance_score": 5.0,
        },
        {
            "source_type": "pdf",
            "resource_id": "pdf_cheatsheet",
            "title": "ML Fundamentals PDF",
            "snippet": "Loss functions measure model empirical risk during optimization.",
            "page_number": 3,
            "relevance_score": 4.0,
        },
    ]

    answer_text, citations, is_refusal, latency_ms = llm_service.generate_grounded_answer(
        question="What is supervised learning?",
        retrieved_contexts=retrieved_contexts,
        current_timestamp=200.0,
    )

    assert is_refusal is False
    assert len(citations) == 2

    # Check Video Citation
    assert citations[0].source_type == "video"
    assert citations[0].timestamp_start == 60.0
    assert citations[0].timestamp_end == 180.0

    # Check PDF Citation
    assert citations[1].source_type == "pdf"
    assert citations[1].page_number == 3

    # Check explicit citation labels in text
    assert "Video 01:00" in answer_text or "Video" in answer_text


def test_llm_service_refusal_when_no_context():
    """
    Test anti-hallucination refusal when context is empty.
    """
    answer_text, citations, is_refusal, latency_ms = llm_service.generate_grounded_answer(
        question="What is the capital of Mars?",
        retrieved_contexts=[],
        current_timestamp=100.0,
    )

    assert is_refusal is True
    assert len(citations) == 0
    assert "do not know" in answer_text.lower()
