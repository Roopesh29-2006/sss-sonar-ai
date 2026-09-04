from fastapi import APIRouter, HTTPException, Path as APIPath
from app.schemas.analysis import StatusResponse, SurveyResultsResponse, DetectionsPerImage
from app.services.analysis_service import analysis_service
from app.services.log_service import log_service
from app.services.inference_service import get_active_inference_provider
from app.schemas.geolocation import TrackPoint

router = APIRouter(prefix="/api/logs", tags=["Analysis"])

@router.post("/{log_id}/analyze")
def start_analysis(log_id: str = APIPath(...)):
    try:
        started = analysis_service.start_analysis_job(log_id)
        provider = get_active_inference_provider()
        return {
            "message": "Analysis started successfully." if started else "Analysis is already processing.",
            "log_id": log_id,
            "status": "PROCESSING",
            "provider": provider.provider_name,
            "is_mock": provider.is_mock
        }
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")

@router.get("/{log_id}/status", response_model=StatusResponse)
def get_analysis_status(log_id: str = APIPath(...)):
    try:
        status_data = analysis_service.get_job_status(log_id)
        # Fetch recent logs list
        logs_list = [l.log_id for l in log_service.get_all_logs()[:5]]
        status_data["recent_logs"] = logs_list
        return StatusResponse(**status_data)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve status: {str(e)}")

@router.get("/{log_id}/results", response_model=SurveyResultsResponse)
def get_survey_results(log_id: str = APIPath(...)):
    detail = log_service.get_log_detail(log_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Survey log '{log_id}' not found.")

    detections_per_img = []
    all_detections = []

    for img in detail.images:
        res = img.analysis_result
        if res:
            dets = res.detections or []
            all_detections.extend(dets)
            known = len([d for d in dets if d.status == "known" or d.class_name == "Shipwreck"])
            unknown = len([d for d in dets if d.status == "unknown" or d.class_name == "Unknown"])
            detections_per_img.append(DetectionsPerImage(
                image_id=img.image_id,
                filename=img.filename,
                image_index=img.image_index,
                detections_count=len(dets),
                known_count=known,
                unknown_count=unknown
            ))

    provider = get_active_inference_provider()

    return SurveyResultsResponse(
        log_id=detail.log_id,
        log_name=detail.log_name,
        status=detail.status,
        total_images=detail.total_images,
        processed_images=detail.processed_images,
        total_detections=detail.total_detections,
        known_count=detail.known_count,
        unknown_count=detail.unknown_count,
        images_with_known_detections=detail.images_with_known_detections,
        images_with_unknown_objects=detail.images_with_unknown_objects,
        high_confidence_count=detail.high_confidence_count,
        average_confidence=detail.average_confidence,
        detections_per_image=detections_per_img,
        all_detections=all_detections,
        location_available=bool(detail.track),
        track=list(detail.track),
        is_mock=provider.is_mock
    )
