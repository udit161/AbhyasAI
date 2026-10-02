import re
from typing import List, Dict, Any, Optional, Union
from app.db.vector_store import vector_store
from app.models.vector_schema import VectorFilterQuery, ResourceType
from app.models.schemas import SourceCitation


def parse_timestamp_to_seconds(timestamp_val: Union[float, int, str]) -> float:
    """
    Parses timestamp input into float seconds.
    Supports float/int numbers (e.g. 1122.0) and formatted strings (e.g. "18:42" or "01:18:42").
    """
    if isinstance(timestamp_val, (int, float)):
        return float(max(0.0, timestamp_val))

    if isinstance(timestamp_val, str):
        timestamp_str = timestamp_val.strip()
        parts = timestamp_str.split(":")
        try:
            if len(parts) == 3:
                h, m, s = float(parts[0]), float(parts[1]), float(parts[2])
                return h * 3600.0 + m * 60.0 + s
            elif len(parts) == 2:
                m, s = float(parts[0]), float(parts[1])
                return m * 60.0 + s
            else:
                return float(max(0.0, float(timestamp_str)))
        except ValueError:
            return 0.0

    return 0.0


def format_seconds_to_timestamp(seconds: float) -> str:
    """
    Formats float seconds into HH:MM:SS or MM:SS timestamp string.
    """
    total_sec = max(0, int(seconds))
    hrs = total_sec // 3600
    mins = (total_sec % 3600) // 60
    secs = total_sec % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


class RetrievalService:
    """
    Retrieval Service enforcing strict timestamp boundary constraints for video transcripts
    while enabling unrestricted grounding retrieval for permitted supporting documents (PDFs, PPTs).
    """

    def retrieve_grounded_context(
        self,
        query: str,
        video_id: str,
        current_timestamp: Union[float, str],
        permitted_doc_ids: Optional[List[str]] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves context chunks strictly constrained to video content watched up to current_timestamp
        (start_time >= 0 and end_time <= current_timestamp), while allowing retrieval from permitted
        supporting PDFs/PPTs without timestamp constraints.
        """
        timestamp_seconds = parse_timestamp_to_seconds(current_timestamp)

        # Build authorized resource ID filter list
        allowed_resources = [video_id]
        if permitted_doc_ids:
            allowed_resources.extend(permitted_doc_ids)

        # Construct vector database metadata filter query
        filter_query = VectorFilterQuery(
            query_text=query,
            video_id=video_id,
            max_timestamp=timestamp_seconds,
            allowed_resource_ids=allowed_resources,
            top_k=top_k,
        )

        # Execute vector database query
        raw_results = vector_store.query(filter_query)

        # Format retrieved results into structured grounding citations
        formatted_results = []
        for item in raw_results:
            source_type = item.get("resource_type", "video")
            res_id = item.get("resource_id", video_id)
            title = item.get("title", "Resource Document")
            snippet = item.get("content", "")
            score = item.get("relevance_score", 0.0)

            start_t = item.get("start_time")
            end_t = item.get("end_time")
            page_num = item.get("page_number")
            slide_idx = item.get("slide_index")

            timestamp_range = None
            if start_t is not None and end_t is not None:
                timestamp_range = f"{format_seconds_to_timestamp(start_t)} - {format_seconds_to_timestamp(end_t)}"

            formatted_results.append(
                {
                    "source_type": source_type,
                    "resource_id": res_id,
                    "title": title,
                    "snippet": snippet,
                    "start_time": start_t,
                    "end_time": end_t,
                    "timestamp_range": timestamp_range,
                    "page_number": page_num,
                    "slide_index": slide_idx,
                    "relevance_score": score,
                }
            )

        return formatted_results


retrieval_service = RetrievalService()
