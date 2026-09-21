from fastapi import APIRouter
from app.api.endpoints import health, learning, ingestion, interview

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(learning.router, prefix="/api/v1", tags=["Learning Assistant"])
api_router.include_router(ingestion.router, prefix="/api/v1", tags=["Multi-Resource Ingestion"])
api_router.include_router(interview.router, prefix="/api/v1", tags=["AI Mock Interview Extension"])
