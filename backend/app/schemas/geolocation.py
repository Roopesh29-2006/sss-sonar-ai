from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LocationInfo(BaseModel):
    latitude: float
    longitude: float
    source: str = "bay_of_bengal_metadata"
    timestamp: Optional[datetime] = None
    match_method: str = "filename"
    match_error_seconds: Optional[float] = None
    location_label: str = "Frame location"


class NavigationRecord(BaseModel):
    image_id: Optional[str] = None
    filename: Optional[str] = None
    frame_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    latitude: float
    longitude: float
    heading: Optional[float] = None
    ping_number: Optional[str] = None


class TrackPoint(BaseModel):
    latitude: float
    longitude: float
    timestamp: Optional[datetime] = None
    source: str = "bay_of_bengal_metadata"
