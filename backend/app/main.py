from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import health, chat

# Initialize FastAPI application
app = FastAPI(
    title="AI Learning Assistant API",
    description="Phase 1 Python FastAPI Backend for AI Learning Assistant Hackathon Project",
    version="1.0.0"
)

# Configure CORS middleware (allows frontend client interaction)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register endpoint routers
app.include_router(health.router)
app.include_router(chat.router)

@app.get("/")
def read_root():
    """
    Root endpoint welcome message and helpful links.
    """
    return {
        "project": "AI Learning Assistant API",
        "phase": "Phase 1 - Core Backend & Mock Q&A",
        "documentation": "/docs",
        "health_check": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
