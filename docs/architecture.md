# Architecture Specification

## Overview

The AI-Powered Interactive Learning Assistant is a production-oriented, timestamp-aware learning system that combines video playback, transcript metadata, PDFs, and PPT slide resources into a unified grounded retrieval pipeline. It also extends to an AI-driven dynamic Mock Interview system.

## Data Flow Architecture

```
[ Video Player (Frontend) ] ── (currentTime: 18:42) ──> [ FastAPI Backend ]
                                                               │
                                                               ▼
[ Permitted Docs (PDF/PPT) ] ──> [ Metadata Ingestion ] ──> [ Timestamp-Aware Vector Retriever ]
                                                               │ (Filter: timestamp <= 18:42)
                                                               ▼
[ Grounded Answer + Citations ] <── [ LLM Reasoning Engine (Bedrock/OpenAI) ]
```

## Key Components

1. **Timestamp-Aware Retrieval Layer**: Filters transcript segments and indexed content strictly up to the active playback timestamp. Prevents spoiler hallucination.
2. **Multi-Resource Ingestion Engine**: Parses VTT/SRT transcripts, PDF pages, and PPT slides with explicit page/slide citation badges.
3. **AI Mock Interview Engine**: Dynamic state machine that adapts interview questions based on candidate answers, role, skill level, and course completed, outputting explainable scorecards.
