import pytest
import os
import shutil
from app.db.vector_store import VectorStoreClient
from app.models.vector_schema import VectorFilterQuery, ResourceType


@pytest.fixture
def temp_vector_store(tmp_path):
    """
    Fixture creating an isolated vector store instance in a temporary folder.
    """
    storage_dir = str(tmp_path / "vector_store")
    client = VectorStoreClient(storage_path=storage_dir)
    yield client


def test_video_timestamp_metadata_filtering(temp_vector_store):
    """
    Test indexing video transcript segments and querying with timestamp range filters.
    """
    video_id = "vid_101"
    segments = [
        {"start_time": 0.0, "end_time": 60.0, "text": "Welcome to Python FastAPI tutorial introduction"},
        {"start_time": 60.0, "end_time": 180.0, "text": "FastAPI request validation using Pydantic models"},
        {"start_time": 180.0, "end_time": 300.0, "text": "Vector Database indexing and timestamp metadata filtering"},
    ]
    
    temp_vector_store.add_video_segments(video_id=video_id, title="FastAPI Course", segments=segments)

    # Query with max_timestamp = 120.0 (Should include segments 0-60 and 60-180, but NOT 180-300)
    query_filter = VectorFilterQuery(
        query_text="FastAPI validation",
        video_id=video_id,
        max_timestamp=120.0,
        resource_types=[ResourceType.VIDEO]
    )
    results = temp_vector_store.query(query_filter)

    assert len(results) > 0
    for res in results:
        assert res["start_time"] <= 120.0


def test_pdf_page_number_metadata_filtering(temp_vector_store):
    """
    Test indexing PDF pages and querying with exact page_number metadata filters.
    """
    doc_id = "pdf_doc_55"
    pages = [
        {"page_number": 1, "text": "Title Page: Machine Learning Architecture Overview"},
        {"page_number": 2, "text": "Chapter 1: Neural Networks and Deep Learning Fundamentals"},
        {"page_number": 3, "text": "Chapter 2: Vector Embeddings and Cosine Similarity Metrics"},
    ]

    temp_vector_store.add_pdf_pages(doc_id=doc_id, title="ML Architecture PDF", pages=pages)

    # Query specifically for page_number = 3
    query_filter = VectorFilterQuery(
        query_text="Embeddings",
        page_number=3,
        resource_types=[ResourceType.PDF]
    )
    results = temp_vector_store.query(query_filter)

    assert len(results) == 1
    assert results[0]["page_number"] == 3
    assert "Cosine Similarity" in results[0]["content"]


def test_ppt_slide_index_metadata_filtering(temp_vector_store):
    """
    Test indexing PPT slides and querying with slide_index metadata filters.
    """
    doc_id = "ppt_deck_99"
    slides = [
        {"slide_index": 1, "text": "Slide 1: Executive Summary of AI Assistant Project"},
        {"slide_index": 2, "text": "Slide 2: System Architecture Diagram and Microservices"},
        {"slide_index": 3, "text": "Slide 3: Cost Evaluation and Benchmark Performance"},
    ]

    temp_vector_store.add_ppt_slides(doc_id=doc_id, title="Executive Presentation", slides=slides)

    # Query specifically for slide_index = 2
    query_filter = VectorFilterQuery(
        query_text="Architecture",
        slide_index=2,
        resource_types=[ResourceType.PPT]
    )
    results = temp_vector_store.query(query_filter)

    assert len(results) == 1
    assert results[0]["slide_index"] == 2
    assert "System Architecture" in results[0]["content"]
