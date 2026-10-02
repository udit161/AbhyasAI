import json
import os
from typing import List, Dict, Any, Optional
from app.db.vector_store import vector_store
from app.services.transcript_chunker import TranscriptChunker
from app.services.embedding_service import embedding_service


class IngestionService:
    """
    Ingestion Service managing the processing pipeline for timestamped video transcripts,
    PDF documents, and PPT slides.
    """

    def process_and_ingest_transcript(
        self,
        video_id: str,
        title: str,
        raw_segments: List[Dict[str, Any]],
        course_id: Optional[str] = None,
        window_duration_seconds: float = 120.0,
        overlap_seconds: float = 30.0,
    ) -> List[Dict[str, Any]]:
        """
        Groups transcript segments into logical sliding-window chunks (e.g. 2-minute blocks),
        generates vector embeddings for each chunk, and stores them in the vector database
        with video_id and timestamp metadata.
        """
        chunker = TranscriptChunker(
            window_duration_seconds=window_duration_seconds,
            overlap_seconds=overlap_seconds,
        )
        chunks = chunker.chunk_transcript(raw_segments)

        # Generate embeddings for each chunk
        for chunk in chunks:
            chunk["embedding"] = embedding_service.generate_embedding(chunk["text"])

        # Store chunks in vector database with metadata
        vector_store.add_video_segments(
            video_id=video_id,
            title=title,
            segments=chunks,
            course_id=course_id,
        )

        return chunks

    def ingest_transcript_json_file(
        self,
        json_file_path: str,
        video_id: str,
        title: str,
        course_id: Optional[str] = None,
        window_duration_seconds: float = 120.0,
        overlap_seconds: float = 30.0,
    ) -> Dict[str, Any]:
        """
        Loads a timestamped video transcript JSON file (with start, end, and text fields),
        chunks it into sliding-window blocks, embeds the text, and persists vectors.
        """
        if not os.path.exists(json_file_path):
            raise FileNotFoundError(f"Transcript JSON file not found at: {json_file_path}")

        with open(json_file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        # Extract list of segments (supports direct list or dict with 'segments' key)
        if isinstance(raw_data, dict) and "segments" in raw_data:
            raw_segments = raw_data["segments"]
        elif isinstance(raw_data, list):
            raw_segments = raw_data
        else:
            raise ValueError("Invalid transcript JSON format. Expected list or dict with 'segments' key.")

        chunks = self.process_and_ingest_transcript(
            video_id=video_id,
            title=title,
            raw_segments=raw_segments,
            course_id=course_id,
            window_duration_seconds=window_duration_seconds,
            overlap_seconds=overlap_seconds,
        )

        return {
            "video_id": video_id,
            "title": title,
            "total_raw_segments": len(raw_segments),
            "chunks_created": len(chunks),
            "chunks": chunks,
        }

    def parse_and_ingest_document(
        self,
        doc_id: str,
        title: str,
        doc_type: str,
        pages: List[Dict[str, Any]],
        course_id: Optional[str] = None,
    ) -> int:
        """
        Ingests PDF/PPT document pages with metadata indexing into vector database.
        """
        if doc_type.lower() == "pdf":
            vector_store.add_pdf_pages(doc_id=doc_id, title=title, pages=pages, course_id=course_id)
        elif doc_type.lower() == "ppt":
            vector_store.add_ppt_slides(doc_id=doc_id, title=title, slides=pages, course_id=course_id)
        return len(pages)

    def ingest_pdf_document(
        self,
        file_path: str,
        doc_id: str,
        title: str,
        course_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extracts PDF pages, chunks text with overlap, tags page_number metadata, and upserts into vector store.
        """
        from app.services.document_processor import document_processor
        return document_processor.process_and_ingest_pdf(
            file_path=file_path,
            doc_id=doc_id,
            title=title,
            course_id=course_id,
        )

    def ingest_ppt_document(
        self,
        file_path: str,
        doc_id: str,
        title: str,
        course_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Extracts PPT slides, chunks text with overlap, tags slide_number metadata, and upserts into vector store.
        """
        from app.services.document_processor import document_processor
        return document_processor.process_and_ingest_ppt(
            file_path=file_path,
            doc_id=doc_id,
            title=title,
            course_id=course_id,
        )


ingestion_service = IngestionService()

