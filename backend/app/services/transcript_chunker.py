import json
from typing import List, Dict, Any, Optional


class TranscriptChunker:
    """
    Sliding-window transcript chunker that groups timestamped transcript segments
    (with start, end, and text fields) into logical time blocks (e.g. 2-minute / 120s windows)
    while preserving precise start and end timestamps.
    """

    def __init__(
        self,
        window_duration_seconds: float = 120.0,
        overlap_seconds: float = 30.0,
        min_chunk_duration_seconds: float = 10.0,
    ):
        self.window_duration_seconds = window_duration_seconds
        self.overlap_seconds = overlap_seconds
        self.min_chunk_duration_seconds = min_chunk_duration_seconds

    def normalize_segments(self, raw_segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalizes input keys to ensure 'start_time', 'end_time', and 'text' exist.
        Supports inputs with keys ('start', 'end', 'text') or ('start_time', 'end_time', 'text').
        """
        normalized = []
        for seg in raw_segments:
            start_val = seg.get("start_time", seg.get("start", 0.0))
            end_val = seg.get("end_time", seg.get("end", 0.0))
            text_val = seg.get("text", "").strip()

            if text_val:
                normalized.append(
                    {
                        "start_time": float(start_val),
                        "end_time": float(end_val),
                        "text": text_val,
                    }
                )

        normalized.sort(key=lambda x: x["start_time"])
        return normalized

    def chunk_transcript(
        self, raw_segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Groups transcript segments into sliding-window chunks.
        Preserves precise start_time of first segment and end_time of last segment.
        """
        segments = self.normalize_segments(raw_segments)
        if not segments:
            return []

        chunks = []
        total_duration = segments[-1]["end_time"]
        step_seconds = max(1.0, self.window_duration_seconds - self.overlap_seconds)

        current_window_start = segments[0]["start_time"]

        while current_window_start < total_duration:
            current_window_end = current_window_start + self.window_duration_seconds

            # Collect all segments overlapping current sliding window
            window_segments = [
                s for s in segments
                if s["start_time"] < current_window_end and s["end_time"] > current_window_start
            ]

            if window_segments:
                chunk_start = window_segments[0]["start_time"]
                chunk_end = window_segments[-1]["end_time"]
                chunk_text = " ".join([s["text"] for s in window_segments])

                # Include chunk if it meets minimum duration requirement or is the only chunk
                if (chunk_end - chunk_start) >= self.min_chunk_duration_seconds or not chunks:
                    chunks.append(
                        {
                            "start_time": round(chunk_start, 2),
                            "end_time": round(chunk_end, 2),
                            "text": chunk_text,
                            "segment_count": len(window_segments),
                        }
                    )

            current_window_start += step_seconds

        return chunks


transcript_chunker = TranscriptChunker()
