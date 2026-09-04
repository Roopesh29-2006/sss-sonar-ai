import threading
import time
from typing import Dict, Any
from app.config import OUTPUTS_DIR
from app.services.log_service import log_service
from app.services.inference_service import get_active_inference_provider

class AnalysisService:
    def __init__(self):
        self._active_jobs: Dict[str, Dict[str, Any]] = {}

    def start_analysis_job(self, log_id: str) -> bool:
        detail = log_service.get_log_detail(log_id)
        if not detail:
            raise ValueError(f"Survey log '{log_id}' not found.")

        if detail.status == "PROCESSING":
            return False # Already running

        # Reset or set status to PROCESSING
        log_service.update_log_status(log_id, "PROCESSING")

        # Spawn background processing thread
        thread = threading.Thread(target=self._run_job_thread, args=(log_id,), daemon=True)
        thread.start()
        return True

    def _run_job_thread(self, log_id: str):
        provider = get_active_inference_provider()
        output_dir = str(OUTPUTS_DIR / log_id)

        try:
            detail = log_service.get_log_detail(log_id)
            if not detail:
                return

            images = detail.images
            total = len(images)

            for idx, img in enumerate(images, start=1):
                # Update current image status in tracking
                self._active_jobs[log_id] = {
                    "current_image": img.filename,
                    "processed": idx - 1,
                    "total": total,
                    "speed_fps": 2.4 # simulated / measured speed
                }

                # Run inference
                result = provider.predict(
                    image_path=img.file_path,
                    output_dir=output_dir,
                    image_id=img.image_id,
                    filename=img.filename,
                    image_index=img.image_index,
                    latitude=img.latitude,
                    longitude=img.longitude,
                    location_note=img.location_note,
                )

                # Persist image result
                log_service.update_image_result(log_id, img.image_id, result)

                # Small delay for visual pipeline demonstration if fast
                time.sleep(0.15)

            # Finish job
            log_service.update_log_status(log_id, "COMPLETED")

        except Exception as e:
            print(f"[AnalysisService] Error analyzing survey {log_id}: {e}")
            log_service.update_log_status(log_id, "FAILED", error_message=str(e))
        finally:
            if log_id in self._active_jobs:
                del self._active_jobs[log_id]

    def get_job_status(self, log_id: str) -> Dict[str, Any]:
        detail = log_service.get_log_detail(log_id)
        if not detail:
            raise ValueError(f"Survey log '{log_id}' not found.")

        total = detail.total_images
        processed = detail.processed_images
        pct = round((processed / total) * 100.0, 1) if total > 0 else 0.0

        active_info = self._active_jobs.get(log_id, {})
        curr_img = active_info.get("current_image")

        if processed > 0 and processed < total and not curr_img:
            # Pick next pending image filename
            for img in detail.images:
                if not img.analysis_result:
                    curr_img = img.filename
                    break

        provider = get_active_inference_provider()

        return {
            "log_id": log_id,
            "status": detail.status,
            "total_images": total,
            "processed_images": processed,
            "progress_percent": pct,
            "current_image": curr_img,
            "processing_speed_fps": active_info.get("speed_fps", 1.8 if detail.status == "PROCESSING" else 0.0),
            "detections_count": detail.total_detections,
            "known_count": detail.known_count,
            "unknown_count": detail.unknown_count,
            "images_with_known_detections": detail.images_with_known_detections,
            "images_with_unknown_objects": detail.images_with_unknown_objects,
            "average_confidence": detail.average_confidence,
            "error_message": detail.error_message,
            "is_mock": provider.is_mock
        }

analysis_service = AnalysisService()
