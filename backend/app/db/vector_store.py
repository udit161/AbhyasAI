import os
import json
from typing import List, Dict, Any, Optional

class TimestampAwareVectorStore:
    """
    Vector store wrapper supporting timestamp metadata filtering:
    Retrieves segments where timestamp <= current_timestamp for videos,
    and associated permitted document pages/slides.
    """
    def __init__(self, storage_path: str = "./data/vector_store"):
        self.storage_path = storage_path
        os.makedirs(self.storage_path, exist_ok=True)
        self.documents: List[Dict[str, Any]] = []
        self._load_documents()

    def _load_documents(self):
        doc_file = os.path.join(self.storage_path, "documents.json")
        if os.path.exists(doc_file):
            try:
                with open(doc_file, "r", encoding="utf-8") as f:
                    self.documents = json.load(f)
            except Exception:
                self.documents = []

    def _save_documents(self):
        doc_file = os.path.join(self.storage_path, "documents.json")
        with open(doc_file, "w", encoding="utf-8") as f:
            json.dump(self.documents, f, indent=2)

    def add_video_segments(self, video_id: str, title: str, segments: List[Dict[str, Any]]):
        for seg in segments:
            self.documents.append({
                "id": f"{video_id}_{seg['start_time']}",
                "resource_id": video_id,
                "resource_title": title,
                "type": "video",
                "content": seg["text"],
                "start_time": seg["start_time"],
                "end_time": seg["end_time"],
                "page_number": None
            })
        self._save_documents()

    def add_document_pages(self, doc_id: str, title: str, doc_type: str, pages: List[Dict[str, Any]]):
        for pg in pages:
            self.documents.append({
                "id": f"{doc_id}_pg{pg['page_number']}",
                "resource_id": doc_id,
                "resource_title": title,
                "type": doc_type,
                "content": pg["text"],
                "start_time": None,
                "end_time": None,
                "page_number": pg["page_number"]
            })
        self._save_documents()

    def query(
        self,
        query_text: str,
        video_id: str,
        max_timestamp: float,
        allowed_resources: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Filtered search:
        - For video segments: start_time <= max_timestamp
        - For documents: resource_id in allowed_resources or associated with current course
        """
        filtered = []
        for doc in self.documents:
            if doc["type"] == "video":
                if doc["resource_id"] == video_id and doc["start_time"] <= max_timestamp:
                    filtered.append(doc)
            else:
                if allowed_resources and doc["resource_id"] in allowed_resources:
                    filtered.append(doc)
                elif not allowed_resources:
                    filtered.append(doc)

        # Simple keyword/relevance match placeholder (upgradeable to embeddings/FAISS)
        query_words = set(query_text.lower().split())
        scored_docs = []
        for doc in filtered:
            doc_words = set(doc["content"].lower().split())
            overlap = len(query_words.intersection(doc_words))
            scored_docs.append((overlap, doc))

        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored_docs[:top_k]]

vector_store = TimestampAwareVectorStore()
