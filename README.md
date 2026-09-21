# AI-Powered Interactive Learning Assistant & Mock Interview System

Production-oriented, timestamp-aware learning assistant integrated with video learning and multi-resource understanding (PDFs, PPTs, Transcripts), extended with an AI-driven dynamic mock interview system.

## System Architecture

- **Frontend**: Vite + React interactive web app featuring timestamp-aware video player, context Q&A panel, quiz generator, and AI mock interview suite.
- **Backend**: FastAPI modular backend providing timestamp-filtered vector retrieval, multi-resource ingestion engine, LLM reasoning service with citations, and interview scorecard generator.
- **Data & Knowledge Layer**: Vector database & hybrid retriever with metadata-based timestamp range filtering (00:00 to current player position).
- **Evaluation Suite**: Benchmark tools testing timestamp boundary compliance, citation grounding accuracy, response latency, and refusal accuracy.

## Project Structure

```
.
├── backend/                # FastAPI application, RAG pipeline, & Interview engine
├── frontend/               # Vite React UI with Video player & AI interaction modules
├── data/                   # Sample videos, transcripts, PDFs, and PPTs
├── evaluation/             # Automated test suite & evaluation scripts
├── docs/                   # Architecture, API specifications, and deployment docs
└── docker-compose.yml      # Local orchestration setup
```

## Quick Start

1. **Backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

2. **Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
