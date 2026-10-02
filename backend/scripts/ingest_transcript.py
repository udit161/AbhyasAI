import sys
import os
import argparse
import json

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.ingestion_service import ingestion_service


def main():
    parser = argparse.ArgumentParser(
        description="Ingest timestamped video transcript JSON file into vector database with sliding-window chunking and vector embeddings."
    )
    parser.add_argument("--file", required=True, help="Path to timestamped transcript JSON file")
    parser.add_argument("--video-id", required=True, help="Unique Video ID")
    parser.add_argument("--title", required=True, help="Video title")
    parser.add_argument("--course-id", default=None, help="Optional Course ID")
    parser.add_argument("--window", type=float, default=120.0, help="Sliding window duration in seconds (default: 120s)")
    parser.add_argument("--overlap", type=float, default=30.0, help="Window overlap in seconds (default: 30s)")

    args = parser.parse_args()

    print(f"[*] Starting transcript ingestion for video: {args.video_id} ('{args.title}')...")
    result = ingestion_service.ingest_transcript_json_file(
        json_file_path=args.file,
        video_id=args.video_id,
        title=args.title,
        course_id=args.course_id,
        window_duration_seconds=args.window,
        overlap_seconds=args.overlap,
    )

    print("[+] Ingestion Completed Successfully!")
    print(f"   - Video ID: {result['video_id']}")
    print(f"   - Total Raw Segments: {result['total_raw_segments']}")
    print(f"   - Chunks Generated & Embedded: {result['chunks_created']}")
    for idx, c in enumerate(result['chunks']):
        print(f"     [Chunk {idx+1}] {c['start_time']}s -> {c['end_time']}s | Text: {c['text'][:65]}...")


if __name__ == "__main__":
    main()
