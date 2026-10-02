import pytest
from app.services.retrieval_service import (
    retrieval_service,
    parse_timestamp_to_seconds,
    format_seconds_to_timestamp,
)
from app.db.vector_store import vector_store


def test_timestamp_parser_utilities():
    """
    Test parsing string timestamps (e.g. "18:42", "01:10:30") and float inputs into seconds.
    """
    assert parse_timestamp_to_seconds(1122.0) == 1122.0
    assert parse_timestamp_to_seconds("18:42") == 1122.0
    assert parse_timestamp_to_seconds("01:10:30") == 4230.0

    assert format_seconds_to_timestamp(1122.0) == "18:42"
    assert format_seconds_to_timestamp(4230.0) == "01:10:30"


def test_timestamp_boundary_filter_prevents_future_content():
    """
    Test that retrieval strictly blocks video chunks where end_time > current_timestamp.
    """
    video_id = "test_vid_timestamp_check"
    title = "Lecture on RAG System Design"

    # Add video transcript segments
    segments = [
        {"start_time": 0.0, "end_time": 600.0, "text": "Segment 1: Overview of RAG architecture fundamentals."},
        {"start_time": 600.0, "end_time": 1120.0, "text": "Segment 2: Timestamp filtering and boundary enforcement in vector store."},
        {"start_time": 1122.0, "end_time": 1800.0, "text": "Segment 3: Advanced future topic spoiler about graph neural networks."},
    ]
    vector_store.add_video_segments(video_id=video_id, title=title, segments=segments)

    # Learner is at 18:42 (1122 seconds)
    results = retrieval_service.retrieve_grounded_context(
        query="vector store",
        video_id=video_id,
        current_timestamp="18:42",
    )

    assert len(results) > 0
    for chunk in results:
        if chunk["source_type"] == "video" and chunk["resource_id"] == video_id:
            # Must strictly satisfy start_time >= 0 and end_time <= 1122.0
            assert chunk["start_time"] >= 0.0
            assert chunk["end_time"] <= 1122.0
            assert "future topic spoiler" not in chunk["snippet"].lower()


def test_supporting_document_retrieval_without_time_constraints():
    """
    Test that permitted PDF and PPT documents are retrieved without timestamp restrictions.
    """
    video_id = "test_vid_with_doc"
    doc_id = "test_pdf_cheatsheet"

    vector_store.add_video_segments(
        video_id=video_id,
        title="Video Lecture",
        segments=[{"start_time": 0.0, "end_time": 300.0, "text": "Video introduction to database queries."}],
    )

    vector_store.add_pdf_pages(
        doc_id=doc_id,
        title="RAG Systems CheatSheet PDF",
        pages=[{"page_number": 5, "text": "Supporting CheatSheet: Query optimization techniques."}],
    )

    results = retrieval_service.retrieve_grounded_context(
        query="Query optimization",
        video_id=video_id,
        current_timestamp=120.0,
        permitted_doc_ids=[doc_id],
    )

    assert len(results) > 0
    pdf_results = [r for r in results if r["resource_id"] == doc_id]
    assert len(pdf_results) == 1
    assert pdf_results[0]["page_number"] == 5
    assert "Query optimization" in pdf_results[0]["snippet"]
