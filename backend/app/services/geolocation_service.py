import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

from app.schemas.geolocation import LocationInfo, NavigationRecord, TrackPoint


class GeolocationService:
    SOURCE = "uploaded_survey_metadata"
    DEFAULT_TIMESTAMP_TOLERANCE_SECONDS = 1.0

    _ALIASES = {
        "image_id": {"image_id", "imageid", "frame_id", "frameid", "frame"},
        "filename": {"filename", "file_name", "image", "image_file", "file"},
        "timestamp": {"timestamp", "time", "datetime", "date_time", "utc_time"},
        "latitude": {"latitude", "lat"},
        "longitude": {"longitude", "lon", "lng"},
        "heading": {"heading", "course", "bearing"},
        "ping_number": {"ping", "ping_number", "ping_id"},
    }

    @staticmethod
    def _normalise_key(value: Any) -> str:
        return str(value).strip().lower().replace(" ", "_").replace("-", "_")

    @staticmethod
    def _parse_timestamp(value: Any) -> Optional[datetime]:
        if value is None or str(value).strip() == "":
            return None
        text = str(value).strip().replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _field_map(self, row: dict[str, Any]) -> dict[str, Any]:
        normalised = {self._normalise_key(key): value for key, value in row.items() if key is not None}
        result: dict[str, Any] = {}
        for target, aliases in self._ALIASES.items():
            for alias in aliases:
                if alias in normalised:
                    result[target] = normalised[alias]
                    break
        return result

    def _record_from_row(self, row: dict[str, Any]) -> NavigationRecord:
        fields = self._field_map(row)
        if "latitude" not in fields or "longitude" not in fields:
            raise ValueError("Metadata records must contain latitude and longitude.")
        latitude = float(fields["latitude"])
        longitude = float(fields["longitude"])
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise ValueError("Metadata coordinates are outside valid latitude/longitude ranges.")
        heading = float(fields["heading"]) if fields.get("heading") not in (None, "") else None
        return NavigationRecord(
            image_id=str(fields["image_id"]).strip() if fields.get("image_id") not in (None, "") else None,
            filename=Path(str(fields["filename"]).strip()).name if fields.get("filename") not in (None, "") else None,
            frame_id=str(fields["image_id"]).strip() if fields.get("image_id") not in (None, "") else None,
            timestamp=self._parse_timestamp(fields.get("timestamp")),
            latitude=latitude,
            longitude=longitude,
            heading=heading,
            ping_number=str(fields["ping_number"]).strip() if fields.get("ping_number") not in (None, "") else None,
        )

    def load_metadata(self, metadata_bytes: bytes, filename: str = "metadata.csv") -> list[NavigationRecord]:
        suffix = Path(filename).suffix.lower()
        try:
            if suffix == ".json":
                payload = json.loads(metadata_bytes.decode("utf-8-sig"))
                if isinstance(payload, dict):
                    payload = payload.get("records", payload.get("navigation", payload.get("data", [])))
                if not isinstance(payload, list):
                    raise ValueError("JSON metadata must contain a list or records/navigation/data list.")
                rows = payload
            else:
                rows = list(csv.DictReader(io.StringIO(metadata_bytes.decode("utf-8-sig"))))
            records = [self._record_from_row(row) for row in rows]
            if not records:
                raise ValueError("Metadata file contains no navigation records.")
            return records
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ValueError(f"Invalid geolocation metadata: {exc}") from exc

    @staticmethod
    def _same(value: Optional[str], candidate: Optional[str]) -> bool:
        return bool(value and candidate and value.strip().lower() == candidate.strip().lower())

    def match(
        self,
        records: Iterable[NavigationRecord],
        image_id: str,
        filename: str,
        image_timestamp: Optional[datetime] = None,
        tolerance_seconds: float = DEFAULT_TIMESTAMP_TOLERANCE_SECONDS,
    ) -> Optional[LocationInfo]:
        record_list = list(records)
        for record in record_list:
            if self._same(record.image_id, image_id) or self._same(record.frame_id, image_id):
                return self._to_location(record, "image_id")
        for record in record_list:
            if self._same(record.filename, Path(filename).name):
                return self._to_location(record, "filename")
        if image_timestamp is not None:
            candidates = [record for record in record_list if record.timestamp is not None]
            if candidates:
                timestamp = image_timestamp if image_timestamp.tzinfo else image_timestamp.replace(tzinfo=timezone.utc)
                nearest = min(candidates, key=lambda record: abs((record.timestamp - timestamp).total_seconds()))
                error = abs((nearest.timestamp - timestamp).total_seconds())
                if error <= tolerance_seconds:
                    return self._to_location(nearest, "timestamp", error)
        return None

    def _to_location(self, record: NavigationRecord, method: str, error: Optional[float] = None) -> LocationInfo:
        return LocationInfo(
            latitude=record.latitude,
            longitude=record.longitude,
            source=self.SOURCE,
            timestamp=record.timestamp,
            match_method=method,
            match_error_seconds=error,
        )

    def track(self, records: Iterable[NavigationRecord]) -> list[TrackPoint]:
        return [TrackPoint(latitude=record.latitude, longitude=record.longitude, timestamp=record.timestamp, source=self.SOURCE) for record in records]


geolocation_service = GeolocationService()