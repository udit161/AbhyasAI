from fastapi import APIRouter
from app.models.schemas import IngestVideoRequest, IngestDocumentRequest
from app.services.ingestion_service import ingestion_service

router = APIRouter()

@router.post("/ingest/video")
def ingest_video(req: IngestVideoRequest):
    # Dummy parsing for sample video transcript
    sample_segments = [
        {"start_time": 0.0, "end_time": 300.0, "text": "Introduction to the course principles, AI systems and setup."},
        {"start_time": 300.0, "end_time": 1122.0, "text": "Deep dive into Timestamp-aware retrieval, video segment metadata indexing, and grounding controls."},
        {"start_time": 1122.0, "end_time": 1800.0, "text": "Vector databases vs Knowledge Graphs, cost optimization, and AWS Bedrock integration strategy."}
    ]
    count = ingestion_service.parse_and_ingest_transcript(req.video_id, req.title, sample_segments)
    return {"status": "success", "video_id": req.video_id, "segments_ingested": count}

@router.post("/ingest/document")
def ingest_document(req: IngestDocumentRequest):
    sample_pages = [
        {"page_number": 1, "text": "Overview of RAG Architecture, chunking strategies, and timestamp metadata filtering."},
        {"page_number": 2, "text": "Evaluation metrics: Retrieval Accuracy, Citation Grounding, Latency, and Cost estimation."}
    ]
    count = ingestion_service.parse_and_ingest_document(req.doc_id, req.title, req.doc_type, sample_pages)
    return {"status": "success", "doc_id": req.doc_id, "pages_ingested": count}
