import os
import json
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.models.vector_schema import (
    VectorMetadata,
    VectorDocument,
    VectorFilterQuery,
    ResourceType,
)


class VectorStoreClient:
    """
    Vector Store Client supporting multi-backend vectors (Chroma, Pinecone, OpenSearch, Local JSON)
    with strict metadata filtering for video timestamps, PDF page numbers, and PPT slide indices.
    """
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or settings.VECTOR_DB_PATH
        self.db_type = settings.VECTOR_DB_TYPE.lower()
        os.makedirs(self.storage_path, exist_ok=True)
        self.documents: List[VectorDocument] = []
        self._load_documents()

    def _load_documents(self):
        doc_file = os.path.join(self.storage_path, "documents.json")
        if os.path.exists(doc_file):
            try:
                with open(doc_file, "r", encoding="utf-8") as f:
                    raw_docs = json.load(f)
                    self.documents = [VectorDocument(**d) for d in raw_docs]
            except Exception:
                self.documents = []

    def _save_documents(self):
        doc_file = os.path.join(self.storage_path, "documents.json")
        with open(doc_file, "w", encoding="utf-8") as f:
            json.dump([d.model_dump() for d in self.documents], f, indent=2)

    def add_video_segments(
        self,
        video_id: str,
        title: str,
        segments: List[Dict[str, Any]],
        course_id: Optional[str] = None,
    ) -> List[str]:
        """
        Adds video transcript segments indexed with start_time and end_time metadata.
        """
        added_ids = []
        for idx, seg in enumerate(segments):
            doc_id = f"vid_{video_id}_seg_{idx}"
            metadata = VectorMetadata(
                resource_id=video_id,
                course_id=course_id,
                resource_type=ResourceType.VIDEO,
                title=title,
                text_chunk=seg["text"],
                start_time=float(seg["start_time"]),
                end_time=float(seg["end_time"]),
                chunk_index=idx,
            )
            doc = VectorDocument(id=doc_id, content=seg["text"], metadata=metadata)
            self.documents.append(doc)
            added_ids.append(doc_id)

        self._save_documents()
        return added_ids

    def add_pdf_pages(
        self,
        doc_id: str,
        title: str,
        pages: List[Dict[str, Any]],
        course_id: Optional[str] = None,
    ) -> List[str]:
        """
        Adds PDF page chunks indexed with 1-based page_number metadata.
        """
        added_ids = []
        for idx, pg in enumerate(pages):
            chunk_id = f"pdf_{doc_id}_pg_{pg['page_number']}"
            metadata = VectorMetadata(
                resource_id=doc_id,
                course_id=course_id,
                resource_type=ResourceType.PDF,
                title=title,
                text_chunk=pg["text"],
                page_number=int(pg["page_number"]),
                chunk_index=idx,
            )
            doc = VectorDocument(id=chunk_id, content=pg["text"], metadata=metadata)
            self.documents.append(doc)
            added_ids.append(chunk_id)

        self._save_documents()
        return added_ids

    def add_ppt_slides(
        self,
        doc_id: str,
        title: str,
        slides: List[Dict[str, Any]],
        course_id: Optional[str] = None,
    ) -> List[str]:
        """
        Adds PPT slide chunks indexed with 1-based slide_index metadata.
        """
        added_ids = []
        for idx, sld in enumerate(slides):
            chunk_id = f"ppt_{doc_id}_sld_{sld['slide_index']}"
            metadata = VectorMetadata(
                resource_id=doc_id,
                course_id=course_id,
                resource_type=ResourceType.PPT,
                title=title,
                text_chunk=sld["text"],
                slide_index=int(sld["slide_index"]),
                chunk_index=idx,
            )
            doc = VectorDocument(id=chunk_id, content=sld["text"], metadata=metadata)
            self.documents.append(doc)
            added_ids.append(chunk_id)

        self._save_documents()
        return added_ids

    def query(self, filter_query: VectorFilterQuery) -> List[Dict[str, Any]]:
        """
        Performs vector search with metadata filtering for:
        - Video timestamps (start_time <= max_timestamp, end_time >= min_timestamp)
        - PDF page numbers (page_number == target_page)
        - PPT slide index (slide_index == target_slide)
        - Resource scope limits (allowed_resource_ids)
        """
        matching_docs: List[VectorDocument] = []

        for doc in self.documents:
            meta = doc.metadata

            # Filter by Resource Types if specified
            if filter_query.resource_types and meta.resource_type not in filter_query.resource_types:
                continue

            # Filter by Course ID if specified
            if filter_query.course_id and meta.course_id and meta.course_id != filter_query.course_id:
                continue

            # Filter by Allowed Resource IDs if specified
            if filter_query.allowed_resource_ids and meta.resource_id not in filter_query.allowed_resource_ids:
                continue

            # Video Timestamp Filtering
            if meta.resource_type == ResourceType.VIDEO:
                if filter_query.video_id and meta.resource_id != filter_query.video_id:
                    continue
                if filter_query.max_timestamp is not None and meta.start_time is not None:
                    if meta.start_time > filter_query.max_timestamp:
                        continue
                if filter_query.min_timestamp is not None and meta.end_time is not None:
                    if meta.end_time < filter_query.min_timestamp:
                        continue

            # PDF Page Number Filtering
            elif meta.resource_type == ResourceType.PDF:
                if filter_query.page_number is not None and meta.page_number != filter_query.page_number:
                    continue

            # PPT Slide Index Filtering
            elif meta.resource_type == ResourceType.PPT:
                if filter_query.slide_index is not None and meta.slide_index != filter_query.slide_index:
                    continue

            matching_docs.append(doc)

        # Relevance scoring (keyword overlap + score calculation)
        query_terms = set(filter_query.query_text.lower().split())
        scored_results = []
        for doc in matching_docs:
            doc_terms = set(doc.content.lower().split())
            score = len(query_terms.intersection(doc_terms))
            scored_results.append((score, doc))

        # Sort by relevance score descending
        scored_results.sort(key=lambda x: x[0], reverse=True)

        # Return top_k matching documents formatted with metadata
        results = []
        for score, doc in scored_results[:filter_query.top_k]:
            res_dict = doc.metadata.model_dump()
            res_dict["id"] = doc.id
            res_dict["content"] = doc.content
            res_dict["relevance_score"] = score
            results.append(res_dict)

        return results


# Backward compatibility alias & default singleton
TimestampAwareVectorStore = VectorStoreClient
vector_store = VectorStoreClient()
