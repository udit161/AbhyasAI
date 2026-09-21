from typing import List, Dict, Any, Optional
from app.db.vector_store import vector_store

class RetrievalService:
    def retrieve_context(
        self,
        query: str,
        video_id: str,
        current_timestamp: float,
        allowed_resources: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves grounded context strictly constrained to content watched up to current_timestamp
        plus explicitly permitted supporting documents (PDFs, PPTs).
        """
        results = vector_store.query(
            query_text=query,
            video_id=video_id,
            max_timestamp=current_timestamp,
            allowed_resources=allowed_resources,
            top_k=5
        )
        return results

retrieval_service = RetrievalService()
