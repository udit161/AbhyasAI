import pytest
from app.services.cache_service import cache_service


def test_cache_service_set_and_get():
    """
    Test setting and retrieving cached responses from Redis/In-Memory Cache.
    """
    cache_key = cache_service.generate_cache_key(
        video_id="vid_cache_test_1",
        current_timestamp=120.0,
        query="What is BM25 hybrid search?",
        permitted_doc_ids=["doc_1", "doc_2"],
    )

    payload = {
        "answer": "Hybrid search combines BM25 keyword matching with dense vector embeddings.",
        "citations": [],
        "is_refusal": False,
    }

    # Verify initial cache miss
    cached_val = cache_service.get_cached_response(cache_key)
    assert cached_val is None

    # Set cache payload
    cache_service.set_cached_response(cache_key, payload, ttl=60)

    # Verify cache hit
    hit_val = cache_service.get_cached_response(cache_key)
    assert hit_val is not None
    assert hit_val["answer"] == payload["answer"]
    assert hit_val["is_refusal"] is False
