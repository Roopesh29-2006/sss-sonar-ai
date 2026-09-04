from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Path as APIPath
from typing import List, Optional
from app.schemas.log import SurveyLogSummary, SurveyLogDetail, ImageRecord
from app.schemas.detection import DetectionItem
from app.services.log_service import log_service
from app.services.geolocation_service import geolocation_service

router = APIRouter(prefix="/api/logs", tags=["Survey Logs"])

@router.post("/upload", response_model=SurveyLogDetail)
async def upload_survey_log(
    files: List[UploadFile] = File(None),
    zip_file: Optional[UploadFile] = File(None),
    metadata_file: Optional[UploadFile] = File(None),
    log_name: Optional[str] = Form(None)
):
    """
    Log-First SSS Survey Log Upload:
    Supports:
    1. Multiple SSS images (PNG, JPG, JPEG, TIF, TIFF)
    2. Single ZIP file containing survey image log
    """
    if zip_file and zip_file.filename:
        if not zip_file.filename.lower().endswith(".zip"):
            raise HTTPException(status_code=400, detail="Uploaded file is not a valid .zip archive.")
        zip_bytes = await zip_file.read()
        if not zip_bytes:
            raise HTTPException(status_code=400, detail="Uploaded ZIP file is empty.")
        try:
            name = log_name or zip_file.filename.rsplit(".", 1)[0]
            metadata = None
            if metadata_file and metadata_file.filename:
                metadata = geolocation_service.load_metadata(await metadata_file.read(), metadata_file.filename)
            return log_service.create_survey_from_zip(
                log_name=name,
                zip_bytes=zip_bytes,
                location_metadata=metadata
            )
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process ZIP archive: {str(e)}")

    if files:
        file_tuples = []
        for f in files:
            if not f.filename:
                continue
            content = await f.read()
            if content:
                file_tuples.append((f.filename, content))

        if not file_tuples:
            raise HTTPException(status_code=400, detail="No valid image files provided.")

        try:
            name = log_name or "Uploaded_Survey_Log"
            metadata = None
            if metadata_file and metadata_file.filename:
                metadata = geolocation_service.load_metadata(await metadata_file.read(), metadata_file.filename)
            return log_service.create_survey_from_files(log_name=name, file_tuples=file_tuples, location_metadata=metadata)
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process uploaded images: {str(e)}")

    raise HTTPException(status_code=400, detail="Please upload either multiple SSS image files or a ZIP archive.")

@router.get("", response_model=List[SurveyLogSummary])
def list_survey_logs():
    return log_service.get_all_logs()

@router.get("/{log_id}", response_model=SurveyLogDetail)
def get_survey_log(log_id: str = APIPath(...)):
    detail = log_service.get_log_detail(log_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Survey log '{log_id}' not found.")
    return detail

@router.get("/{log_id}/images", response_model=List[ImageRecord])
def get_survey_images(log_id: str = APIPath(...)):
    detail = log_service.get_log_detail(log_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Survey log '{log_id}' not found.")
    return detail.images

@router.get("/{log_id}/images/{image_id}", response_model=ImageRecord)
def get_survey_image_detail(log_id: str = APIPath(...), image_id: str = APIPath(...)):
    detail = log_service.get_log_detail(log_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Survey log '{log_id}' not found.")
    for img in detail.images:
        if img.image_id == image_id:
            return img
    raise HTTPException(status_code=404, detail=f"Image '{image_id}' not found in survey log '{log_id}'.")

@router.get("/{log_id}/detections", response_model=List[DetectionItem])
def get_survey_detections(log_id: str = APIPath(...)):
    detail = log_service.get_log_detail(log_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Survey log '{log_id}' not found.")

    all_dets = []
    for img in detail.images:
        if img.analysis_result and img.analysis_result.detections:
            all_dets.extend(img.analysis_result.detections)
    return all_dets
