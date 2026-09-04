from pydantic import BaseModel
from typing import List, Optional
from app.schemas.detection import DetectionItem
from app.schemas.geolocation import TrackPoint

class StatusResponse(BaseModel):
    log_id: str
    status: str
    total_images: int
    processed_images: int
    progress_percent: float
    current_image: Optional[str] = None
    processing_speed_fps: float = 0.0
    detections_count: int = 0
    known_count: int = 0
    unknown_count: int = 0
    images_with_known_detections: int = 0
    images_with_unknown_objects: int = 0
    average_confidence: float = 0.0
    recent_logs: List[str] = []
    error_message: Optional[str] = None
    is_mock: bool = True

class DetectionsPerImage(BaseModel):
    image_id: str
    filename: str
    image_index: int
    detections_count: int
    known_count: int
    unknown_count: int

class SurveyResultsResponse(BaseModel):
    log_id: str
    log_name: str
    status: str
    total_images: int
    processed_images: int
    total_detections: int
    known_count: int
    unknown_count: int
    images_with_known_detections: int = 0
    images_with_unknown_objects: int = 0
    high_confidence_count: int
    average_confidence: float
    detections_per_image: List[DetectionsPerImage] = []
    all_detections: List[DetectionItem] = []
    location_available: bool = False
    track: List[TrackPoint] = []
    is_mock: bool = True
