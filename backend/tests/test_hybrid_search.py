import pytest
from app.db.vector_store import VectorStoreClient
from app.models.vector_schema import VectorFilterQuery, ResourceType


@pytest.fixture
def hybrid_vector_store(tmp_path):
    storage_dir = str(tmp_path / "hybrid_store")
    return VectorStoreClient(storage_path=storage_dir)


def test_hybrid_search_bm25_exact_code_term(hybrid_vector_store):
    """
    Test that hybrid search scores exact code terms and technical keywords high using BM25 + Vector Similarity.
    """
    video_id = "vid_tech_terms"
    segments = [
        {"start_time": 0.0, "end_time": 60.0, "text": "Basic introduction to web API frameworks in Python."},
        {"start_time": 60.0, "end_time": 120.0, "text": "Specific technical term: SQLAlchemy mapped_column ORM metadata declaration."},
        {"start_time": 120.0, "end_time": 180.0, "text": "General database connection strings and pooling parameters."},
    ]
    hybrid_vector_store.add_video_segments(video_id=video_id, title="FastAPI Course", segments=segments)

    # Query with exact technical keyword "mapped_column"
    query_filter = VectorFilterQuery(
        query_text="mapped_column",
        video_id=video_id,
        max_timestamp=180.0,
        resource_types=[ResourceType.VIDEO]
    )

    results = hybrid_vector_store.query(query_filter)

    assert len(results) > 0
    # Top result must be Segment 2 containing exact BM25 keyword "mapped_column"
    assert "mapped_column" in results[0]["content"]
    assert results[0]["relevance_score"] > 0.0
