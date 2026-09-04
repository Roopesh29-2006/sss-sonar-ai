from fastapi import APIRouter
from app.services.inference_service import get_active_inference_provider

router = APIRouter(tags=["Health"])

@router.get("/api/health")
def health_check():
    provider = get_active_inference_provider()
    return {
        "status": "healthy",
        "system": "SonarAI Side-Scan Sonar Analysis API",
        "version": "1.0.0",
        "inference_provider": provider.provider_name,
        "is_mock": provider.is_mock,
        "weights_ready": not provider.is_mock
    }
