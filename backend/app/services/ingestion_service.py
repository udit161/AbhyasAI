from typing import List, Dict, Any
from app.db.vector_store import vector_store

class IngestionService:
    def parse_and_ingest_transcript(self, video_id: str, title: str, transcript_lines: List[Dict[str, Any]]) -> int:
        """
        Parses VTT/SRT timestamped lines and stores them in timestamp-aware vector store.
        transcript_lines example: [{"start_time": 0.0, "end_time": 15.2, "text": "Welcome to machine learning..."}]
        """
        vector_store.add_video_segments(video_id, title, transcript_lines)
        return len(transcript_lines)

    def parse_and_ingest_document(self, doc_id: str, title: str, doc_type: str, pages: List[Dict[str, Any]]) -> int:
        """
        Ingests PDF/PPT pages/slides with slide or page numbers into vector store.
        pages example: [{"page_number": 1, "text": "Slide 1: Gradient Descent Principles..."}]
        """
        vector_store.add_document_pages(doc_id, title, doc_type, pages)
        return len(pages)

ingestion_service = IngestionService()
