from fastapi import APIRouter
from app.database import engine
from app.services.llm_service import client
from app.config import config
import httpx

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

@router.get("/health/detailed")
async def detailed_health_check():
    status_report = {
        "status": "healthy",
        "database": "unknown",
        "llm": "unknown",
        "weather_api": "configured" if config.WEATHER_API_KEY else "missing_key",
        "search_api": "configured" if config.TAVILY_API_KEY else "missing_key",
        "service": "VoxAI Backend"
    }
    
    # Check DB
    try:
        async with engine.connect() as conn:
            status_report["database"] = "healthy"
    except Exception as e:
        status_report["database"] = f"unhealthy: {str(e)}"
        status_report["status"] = "degraded"
        
    # Check LLM (just a fast models list check to verify API key)
    try:
        await client.models.list()
        status_report["llm"] = "healthy"
    except Exception as e:
        status_report["llm"] = f"unhealthy: {str(e)}"
        status_report["status"] = "degraded"
        
    return status_report
