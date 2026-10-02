import pytest
import os
from app.services.ingestion_service import ingestion_service
from app.db.vector_store import vector_store
from app.models.vector_schema import VectorFilterQuery, ResourceType


def test_transcript_json_ingestion_pipeline():
    """
    Test full end-to-end transcript ingestion pipeline from JSON file to vector DB storage.
    """
    sample_json_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "..",
        "data",
        "sample_transcripts",
        "sample_lecture.json"
    )
    sample_json_path = os.path.abspath(sample_json_path)

    video_id = "test_vid_pipeline_999"
    title = "Sample RAG Architecture Lecture"

    # Ingest JSON file
    result = ingestion_service.ingest_transcript_json_file(
        json_file_path=sample_json_path,
        video_id=video_id,
        title=title,
        window_duration_seconds=120.0,
        overlap_seconds=30.0,
    )

    assert result["video_id"] == video_id
    assert result["total_raw_segments"] == 6
    assert result["chunks_created"] >= 2

    # Query Vector Database to verify chunks were embedded and saved with timestamp metadata
    query_filter = VectorFilterQuery(
        query_text="timestamp metadata",
        video_id=video_id,
        max_timestamp=200.0,
        resource_types=[ResourceType.VIDEO]
    )
    search_results = vector_store.query(query_filter)

    assert len(search_results) > 0
    assert search_results[0]["resource_id"] == video_id
    assert search_results[0]["start_time"] is not None
    assert search_results[0]["end_time"] is not None
    assert search_results[0]["start_time"] <= 200.0
