from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.geolocation import LocationInfo

class BoundingBox(BaseModel):
    xmin: float
    ymin: float
    xmax: float
    ymax: float

class SegmentationArea(BaseModel):
    pixel_count: int
    contour_points: List[List[float]] = [] # list of [x, y] coordinates

class DetectionItem(BaseModel):
    object_id: str
    class_name: str # e.g. "shipwreck", "unknown_object"
    status: str = "known"
    confidence: Optional[float] = None
    novelty_score: Optional[float] = None
    bbox: BoundingBox
    segmentation: SegmentationArea
    location: Optional[LocationInfo] = None
    is_mock: bool = True

class SSLFeatures(BaseModel):
    feature_vector: List[float] = [] # e.g. 128-dim SSL embedding
    similarity_score: float = 0.0
    novelty_score: float = 0.0
    is_mock: bool = True

class ImageAnalysisResult(BaseModel):
    image_id: str
    filename: str
    image_index: int
    width: int
    height: int
    original_url: str
    mask_url: str
    overlay_url: str
    thumbnail_url: str
    detections: List[DetectionItem] = []
    known_detections: List[DetectionItem] = []
    unknown_detections: List[DetectionItem] = []
    ssl_features: SSLFeatures
    processing_time_ms: float
    location_available: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_note: str = "Location data unavailable"
    location: Optional[LocationInfo] = None
    is_mock: bool = True
