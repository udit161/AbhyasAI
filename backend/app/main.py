from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import health, chat

# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Python FastAPI Backend for AI Learning Assistant & Mock Interview Platform",
    version="1.0.0",
    debug=settings.DEBUG,
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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
        "project": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "documentation": "/docs",
        "health_check": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)

