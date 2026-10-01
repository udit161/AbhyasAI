from fastapi import APIRouter

router = APIRouter(tags=["Health Check"])

@router.get("/health")
def get_health_status():
    """
    GET /health
    Health check endpoint returning {"status": "ok"}.
    Used to verify that the API server is up and running.
    """
    return {"status": "ok"}
