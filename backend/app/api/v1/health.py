from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app_env": settings.APP_ENV,
        "app_name": settings.APP_NAME,
        "version": "1.0.0"
    }


@router.get("/ready")
async def readiness_check():
    # Verify connections / stores are ready
    return {
        "status": "ready",
        "vector_store": settings.VECTOR_STORE,
        "llm_provider": settings.LLM_PROVIDER,
        "embedding_provider": settings.EMBEDDING_PROVIDER
    }
