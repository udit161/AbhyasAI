import pytest
from app.services.transcript_chunker import TranscriptChunker


def test_transcript_chunker_sliding_window():
    """
    Test grouping transcript segments into sliding windows with start and end timestamp preservation.
    """
    raw_segments = [
        {"start": 0.0, "end": 20.0, "text": "Segment 1: Introduction to AI systems."},
        {"start": 20.0, "end": 50.0, "text": "Segment 2: Overview of vector search engines."},
        {"start": 50.0, "end": 90.0, "text": "Segment 3: Chunking transcript audio streams."},
        {"start": 90.0, "end": 140.0, "text": "Segment 4: Preserving start and end timestamps."},
        {"start": 140.0, "end": 200.0, "text": "Segment 5: Advanced metadata filtering in RAG."},
    ]

    # Initialize chunker with 120-second window, 30-second overlap
    chunker = TranscriptChunker(window_duration_seconds=120.0, overlap_seconds=30.0)
    chunks = chunker.chunk_transcript(raw_segments)

    assert len(chunks) >= 2

    # Verify First Chunk
    first_chunk = chunks[0]
    assert first_chunk["start_time"] == 0.0
    assert first_chunk["end_time"] >= 90.0
    assert "Introduction to AI systems" in first_chunk["text"]

    # Verify Second Chunk Start & End Preservation
    second_chunk = chunks[1]
    assert second_chunk["start_time"] > 0.0
    assert second_chunk["end_time"] == 200.0
    assert "metadata filtering" in second_chunk["text"].lower()



def test_transcript_chunker_handles_different_key_names():
    """
    Test that chunker seamlessly handles both ('start', 'end') and ('start_time', 'end_time').
    """
    raw_segments = [
        {"start_time": 10.0, "end_time": 40.0, "text": "Testing start_time and end_time key format."},
        {"start": 40.0, "end": 80.0, "text": "Testing start and end key format."},
    ]

    chunker = TranscriptChunker(window_duration_seconds=100.0)
    chunks = chunker.chunk_transcript(raw_segments)

    assert len(chunks) == 1
    assert chunks[0]["start_time"] == 10.0
    assert chunks[0]["end_time"] == 80.0
    assert "start_time and end_time" in chunks[0]["text"]
    assert "start and end" in chunks[0]["text"]
