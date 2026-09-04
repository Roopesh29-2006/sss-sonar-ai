import json
import os
import shutil
import zipfile
import uuid
import re
import csv
import io
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from PIL import Image

from app.config import UPLOADS_DIR, OUTPUTS_DIR, DATA_FILE, ALLOWED_EXTENSIONS
from app.schemas.log import SurveyLogDetail, SurveyLogSummary, ImageRecord
from app.schemas.detection import ImageAnalysisResult
from app.schemas.geolocation import LocationInfo, NavigationRecord
from app.services.geolocation_service import geolocation_service

class LogService:
    def __init__(self):
        self._db: Dict[str, Dict[str, Any]] = {}
        self._load_from_disk()
        if not self._db:
            self._seed_demo_survey()

    def _load_from_disk(self):
        if DATA_FILE.exists():
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._db = data
            except Exception as e:
                print(f"[LogService] Error loading DB file: {e}")

    def _save_to_disk(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self._db, f, indent=2, default=str)
        except Exception as e:
            print(f"[LogService] Error saving DB file: {e}")

    def _seed_demo_survey(self):
        """Seed a realistic DEMO survey log on first initialization so UI is functional right away."""
        log_id = "survey_demo_001"
        log_dir = UPLOADS_DIR / log_id
        log_dir.mkdir(parents=True, exist_ok=True)
        out_dir = OUTPUTS_DIR / log_id
        out_dir.mkdir(parents=True, exist_ok=True)

        images = []
        for i in range(1, 13): # 12 sample sonar images
            fname = f"sonar_{i:03d}.png"
            fpath = log_dir / fname
            # Generate sample sonar image if not present
            if not fpath.exists():
                img = Image.new("RGB", (640, 360), color=(15, 25, 40))
                img.save(fpath)

            img_id = f"{log_id}_img_{i:03d}"
            images.append({
                "image_id": img_id,
                "filename": fname,
                "image_index": i,
                "file_path": str(fpath),
                "original_url": f"/api/storage/uploads/{log_id}/{fname}",
                "upload_timestamp": datetime.utcnow().isoformat(),
                "file_size_bytes": os.path.getsize(fpath),
                "analysis_result": None
            })

        self._db[log_id] = {
            "log_id": log_id,
            "log_name": "Survey_Demo_Shipwreck_Area",
            "total_images": len(images),
            "upload_timestamp": datetime.utcnow().isoformat(),
            "status": "UPLOADED",
            "processed_images": 0,
            "total_detections": 0,
            "known_count": 0,
            "unknown_count": 0,
            "images_with_known_detections": 0,
            "images_with_unknown_objects": 0,
            "high_confidence_count": 0,
            "average_confidence": 0.0,
            "error_message": None,
            "images": images
        }
        self._save_to_disk()

    def get_all_logs(self) -> List[SurveyLogSummary]:
        self._load_from_disk()
        results = []
        for log_id, record in self._db.items():
            results.append(SurveyLogSummary(
                log_id=record["log_id"],
                log_name=record["log_name"],
                total_images=record["total_images"],
                upload_timestamp=datetime.fromisoformat(record["upload_timestamp"]),
                status=record.get("status", "UPLOADED"),
                processed_images=record.get("processed_images", 0),
                total_detections=record.get("total_detections", 0),
                known_count=record.get("known_count", 0),
                unknown_count=record.get("unknown_count", 0),
                images_with_known_detections=record.get("images_with_known_detections", 0),
                images_with_unknown_objects=record.get("images_with_unknown_objects", 0),
                high_confidence_count=record.get("high_confidence_count", 0),
                average_confidence=record.get("average_confidence", 0.0)
            ))
        # Sort newest first
        results.sort(key=lambda x: x.upload_timestamp, reverse=True)
        return results

    def get_log_detail(self, log_id: str) -> Optional[SurveyLogDetail]:
        record = self._db.get(log_id)
        if not record:
            self._load_from_disk()
            record = self._db.get(log_id)

        if not record:
            return None
        return SurveyLogDetail(
            log_id=record["log_id"],
            log_name=record["log_name"],
            total_images=record["total_images"],
            upload_timestamp=datetime.fromisoformat(record["upload_timestamp"]),
            status=record.get("status", "UPLOADED"),
            processed_images=record.get("processed_images", 0),
            total_detections=record.get("total_detections", 0),
            known_count=record.get("known_count", 0),
            unknown_count=record.get("unknown_count", 0),
            images_with_known_detections=record.get("images_with_known_detections", 0),
            images_with_unknown_objects=record.get("images_with_unknown_objects", 0),
            high_confidence_count=record.get("high_confidence_count", 0),
            average_confidence=record.get("average_confidence", 0.0),
            error_message=record.get("error_message"),
            track=record.get("track", []),
            images=[ImageRecord(**img) for img in record.get("images", [])]
        )

    @staticmethod
    def parse_location_metadata(metadata_bytes: bytes, filename: str = "metadata.csv") -> List[NavigationRecord]:
        return geolocation_service.load_metadata(metadata_bytes, filename)

    def create_survey_from_files(self, log_name: str, file_tuples: List[tuple], custom_log_id: Optional[str] = None, location_metadata: Optional[List[NavigationRecord]] = None) -> SurveyLogDetail:
        """
        file_tuples: list of (filename, bytes_content)
        """
        log_id = custom_log_id or f"survey_{uuid.uuid4().hex[:8]}"
        log_dir = UPLOADS_DIR / log_id
        log_dir.mkdir(parents=True, exist_ok=True)

        # Sort file tuples deterministically by filename using natural sort
        def natural_sort_key(s):
            return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s[0])]

        sorted_files = sorted(file_tuples, key=natural_sort_key)

        images = []
        location_records = location_metadata or []
        for idx, (fname, content) in enumerate(sorted_files, start=1):
            ext = Path(fname).suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                continue

            safe_name = Path(fname).name
            target_path = log_dir / safe_name
            with open(target_path, "wb") as f:
                f.write(content)

            img_id = f"{log_id}_img_{idx:03d}"
            location = geolocation_service.match(location_records, img_id, safe_name)
            images.append({
                "image_id": img_id,
                "filename": safe_name,
                "image_index": idx,
                "file_path": str(target_path),
                "original_url": f"/api/storage/uploads/{log_id}/{safe_name}",
                "upload_timestamp": datetime.utcnow().isoformat(),
                "file_size_bytes": len(content),
                "latitude": location.latitude if location else None,
                "longitude": location.longitude if location else None,
                "location_note": "GPS Available - Frame location" if location else "Location data unavailable",
                "location": location.model_dump(mode="json") if location else None,
                "analysis_result": None
            })

        if not images:
            raise ValueError("No valid image files found in upload.")

        record = {
            "log_id": log_id,
            "log_name": log_name or f"Survey_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "total_images": len(images),
            "upload_timestamp": datetime.utcnow().isoformat(),
            "status": "UPLOADED",
            "processed_images": 0,
            "total_detections": 0,
            "known_count": 0,
            "unknown_count": 0,
            "images_with_known_detections": 0,
            "images_with_unknown_objects": 0,
            "high_confidence_count": 0,
            "average_confidence": 0.0,
            "error_message": None,
            "track": [point.model_dump(mode="json") for point in geolocation_service.track(location_records)],
            "images": images
        }
        self._db[log_id] = record
        self._save_to_disk()
        return self.get_log_detail(log_id)

    def create_survey_from_zip(
        self,
        log_name: str,
        zip_bytes: bytes,
        location_metadata: Optional[List[NavigationRecord]] = None
    ) -> SurveyLogDetail:
        """
        Safely extract ZIP archive, filter images, preserve deterministic order.
        """
        temp_zip_path = UPLOADS_DIR / f"temp_{uuid.uuid4().hex}.zip"
        with open(temp_zip_path, "wb") as f:
            f.write(zip_bytes)

        file_tuples = []
        parsed_location_metadata = list(location_metadata or [])
        try:
            with zipfile.ZipFile(temp_zip_path, "r") as z:
                for member in z.infolist():
                    if member.is_dir():
                        continue
                    # Safe filename (prevent path traversal)
                    fname = Path(member.filename).name
                    if fname.lower() in {"metadata.csv", "locations.csv", "gps.csv", "metadata.json", "locations.json", "gps.json"}:
                        parsed_location_metadata.extend(self.parse_location_metadata(z.read(member), fname))
                        continue
                    if not fname or fname.startswith("."):
                        continue
                    ext = Path(fname).suffix.lower()
                    if ext in ALLOWED_EXTENSIONS:
                        content = z.read(member)
                        file_tuples.append((fname, content))
        finally:
            if temp_zip_path.exists():
                os.remove(temp_zip_path)

        if not file_tuples:
            raise ValueError("ZIP archive contains no supported SSS image files (PNG, JPG, TIF, TIFF).")

        return self.create_survey_from_files(
            log_name=log_name,
            file_tuples=file_tuples,
            location_metadata=parsed_location_metadata
        )

    def update_log_status(self, log_id: str, status: str, error_message: Optional[str] = None):
        self._load_from_disk()
        if log_id in self._db:
            self._db[log_id]["status"] = status
            if error_message:
                self._db[log_id]["error_message"] = error_message
            self._save_to_disk()

    def update_image_result(self, log_id: str, image_id: str, result: ImageAnalysisResult):
        self._load_from_disk()
        if log_id not in self._db:
            return

        log = self._db[log_id]
        for img in log["images"]:
            if img["image_id"] == image_id:
                location = img.get("location")
                if location:
                    typed_location = LocationInfo(**location)
                    result.location = typed_location
                    for detection in result.detections:
                        detection.location = typed_location
                    for detection in result.known_detections:
                        detection.location = typed_location
                    for detection in result.unknown_detections:
                        detection.location = typed_location
                img["analysis_result"] = result.model_dump() if hasattr(result, "model_dump") else result.dict()
                break

        # Re-compute summary stats
        processed = [i for i in log["images"] if i["analysis_result"] is not None]
        log["processed_images"] = len(processed)

        all_dets = []
        conf_scores = []
        for i in processed:
            res = i["analysis_result"]
            if res and "detections" in res:
                for d in res["detections"]:
                    all_dets.append(d)
                    if d.get("confidence") is not None:
                        conf_scores.append(d["confidence"])

        log["total_detections"] = len(all_dets)
        log["known_count"] = len([d for d in all_dets if d.get("status") == "known" or d.get("class_name") == "Shipwreck"])
        log["unknown_count"] = len([d for d in all_dets if d.get("status") == "unknown" or d.get("class_name") == "Unknown"])
        log["images_with_known_detections"] = sum(
            1 for i in processed
            if any(d.get("status") == "known" or d.get("class_name") == "Shipwreck" for d in i["analysis_result"].get("detections", []))
        )
        log["images_with_unknown_objects"] = sum(
            1 for i in processed
            if any(d.get("status") == "unknown" or d.get("class_name") == "Unknown" for d in i["analysis_result"].get("detections", []))
        )
        log["high_confidence_count"] = len([d for d in all_dets if d.get("confidence") is not None and d["confidence"] >= 0.85])
        log["average_confidence"] = round(sum(conf_scores) / len(conf_scores), 3) if conf_scores else 0.0

        if log["processed_images"] == log["total_images"]:
            log["status"] = "COMPLETED"

        self._save_to_disk()

log_service = LogService()
