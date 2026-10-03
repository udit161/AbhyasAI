import json
import argparse
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# Constants for sliding window (in seconds)
MAX_WINDOW_DURATION = 120.0  # 2 minutes
WINDOW_OVERLAP = 30.0        # 30 seconds overlap

def chunk_transcript(segments: List[Dict[str, Any]], max_duration: float, overlap: float) -> List[Dict[str, Any]]:
    """
    Groups contiguous segments into blocks of approx `max_duration` seconds, 
    sliding by `max_duration - overlap` to create rolling contexts.
    """
    chunks = []
    current_chunk = []
    current_start = segments[0]['start'] if segments else 0.0
    
    i = 0
    while i < len(segments):
        seg = segments[i]
        
        # If adding this segment exceeds our target duration, save the chunk and slide
        if current_chunk and (seg['end'] - current_start > max_duration):
            # Finalize current chunk
            chunk_text = " ".join([s['text'] for s in current_chunk])
            chunks.append({
                "text": chunk_text,
                "start_time": current_start,
                "end_time": current_chunk[-1]['end']
            })
            
            # Slide the window forward by finding the first segment in the current chunk 
            # that is past the overlap threshold
            overlap_threshold = current_chunk[-1]['end'] - overlap
            
            # Backtrack 'i' to the first segment that starts after the overlap threshold
            backtrack_index = i
            for j in range(len(current_chunk)):
                if current_chunk[j]['start'] >= overlap_threshold:
                    backtrack_index = i - len(current_chunk) + j
                    break
                    
            # If we didn't backtrack at all (edge case with very long segments), just move forward by 1
            if backtrack_index == i:
                backtrack_index = i - len(current_chunk) + 1
                
            i = backtrack_index
            current_chunk = []
            if i < len(segments):
                current_start = segments[i]['start']
            continue
            
        # Add to current chunk
        current_chunk.append(seg)
        i += 1
        
    # Add the last lingering chunk
    if current_chunk:
        chunk_text = " ".join([s['text'] for s in current_chunk])
        chunks.append({
            "text": chunk_text,
            "start_time": current_start,
            "end_time": current_chunk[-1]['end']
        })
        
    return chunks

def process_and_store(input_json: str, video_id: str, db_path: str = "./chroma_db"):
    # 1. Load JSON segments
    with open(input_json, 'r', encoding='utf-8') as f:
        segments = json.load(f)
        
    print(f"Loaded {len(segments)} segments. Chunking...")
    
    # 2. Chunk with sliding window
    chunks = chunk_transcript(segments, max_duration=MAX_WINDOW_DURATION, overlap=WINDOW_OVERLAP)
    print(f"Created {len(chunks)} sliding window chunks.")
    
    # 3. Initialize Embedding Model (Open-source HuggingFace model)
    print("Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # 4. Generate Embeddings
    print("Generating embeddings...")
    texts = [c['text'] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True).tolist()
    
    # 5. Store in Vector Database (ChromaDB)
    print("Initializing ChromaDB...")
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection(name="video_transcripts")
    
    ids = [f"{video_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{
        "video_id": video_id,
        "start_time": c['start_time'],
        "end_time": c['end_time']
    } for c in chunks]
    
    print("Storing embeddings to database...")
    collection.add(
        ids=ids,
        embeddings=embeddings,
        metadatas=metadatas,
        documents=texts
    )
    
    print(f"Successfully stored {len(chunks)} vectorized chunks for video_id: {video_id}!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process video transcript into vector db.")
    parser.add_argument("--input", required=True, help="Path to input JSON containing transcript segments")
    parser.add_argument("--video_id", required=True, help="Unique identifier for the video")
    parser.add_argument("--db_path", default="./chroma_db", help="Path to store vector database")
    
    args = parser.parse_args()
    process_and_store(args.input, args.video_id, args.db_path)
