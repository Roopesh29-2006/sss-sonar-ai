from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.schemas.detection import ImageAnalysisResult
from app.schemas.geolocation import LocationInfo, TrackPoint

class ImageRecord(BaseModel):
    image_id: str
    filename: str
    image_index: int
    file_path: str
    original_url: str
    upload_timestamp: datetime
    file_size_bytes: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_note: str = "Location data unavailable"
    location: Optional[LocationInfo] = None
    analysis_result: Optional[ImageAnalysisResult] = None

class SurveyLogBase(BaseModel):
    log_id: str
    log_name: str
    total_images: int
    upload_timestamp: datetime
    status: str = "UPLOADED" # UPLOADED, PROCESSING, COMPLETED, FAILED

class SurveyLogSummary(SurveyLogBase):
    processed_images: int = 0
    total_detections: int = 0
    known_count: int = 0
    unknown_count: int = 0
    images_with_known_detections: int = 0
    images_with_unknown_objects: int = 0
    high_confidence_count: int = 0
    average_confidence: float = 0.0

class SurveyLogDetail(SurveyLogSummary):
    images: List[ImageRecord] = []
    error_message: Optional[str] = None
    track: List[TrackPoint] = []
