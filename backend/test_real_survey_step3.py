import json
import time
from pathlib import Path

import requests

BASE_URL = "http://127.0.0.1:8000"
BACKEND_DIR = Path(__file__).resolve().parent
IMAGE_PATHS = [
    BACKEND_DIR / "test_dataimages" / "images" / "Viator_071.png",
    BACKEND_DIR / "test_dataimages" / "images" / "Monohansett_01.png",
    BACKEND_DIR / "app" / "storage" / "uploads" / "survey_afad75f5" / "sonar_zip_03.png",
]


def main() -> None:
    files = [("files", (path.name, path.read_bytes(), "image/png")) for path in IMAGE_PATHS]
    upload = requests.post(
        f"{BASE_URL}/api/logs/upload",
        files=files,
        data={"log_name": "Step3_Real_SSS_Survey"},
        timeout=30,
    )
    upload.raise_for_status()
    log_id = upload.json()["log_id"]
    requests.post(f"{BASE_URL}/api/logs/{log_id}/analyze", timeout=30).raise_for_status()

    statuses = []
    for _ in range(120):
        status = requests.get(f"{BASE_URL}/api/logs/{log_id}/status", timeout=30).json()
        statuses.append({key: status[key] for key in (
            "status", "processed_images", "total_images", "progress_percent",
            "current_image", "known_count", "unknown_count",
        )})
        if status["status"] in {"COMPLETED", "FAILED"}:
            break
        time.sleep(1)

    if status["status"] != "COMPLETED":
        raise RuntimeError(f"Survey did not complete: {status}")

    results_response = requests.get(f"{BASE_URL}/api/logs/{log_id}/results", timeout=30)
    results_response.raise_for_status()
    results = results_response.json()
    images_response = requests.get(f"{BASE_URL}/api/logs/{log_id}/images", timeout=30)
    images_response.raise_for_status()
    images = images_response.json()
    if len(images) != len(IMAGE_PATHS) or any(image["analysis_result"] is None for image in images):
        raise RuntimeError("Completed survey contains an unprocessed image result")

    overlays = []
    for image in images:
        detail = requests.get(
            f"{BASE_URL}/api/logs/{log_id}/images/{image['image_id']}",
            timeout=30,
        ).json()
        overlay_url = detail["analysis_result"]["overlay_url"]
        overlay_response = requests.get(f"{BASE_URL}{overlay_url}", timeout=30)
        overlay_response.raise_for_status()
        overlays.append({"filename": image["filename"], "overlay_url": overlay_url})

    output = {
        "log_id": log_id,
        "statuses": statuses,
        "results_summary": {
            key: results[key]
            for key in (
                "status", "total_images", "processed_images", "total_detections",
                "known_count", "unknown_count", "images_with_known_detections",
                "images_with_unknown_objects",
            )
        },
        "image_results": [
            {
                "filename": image["filename"],
                "image_id": image["image_id"],
                "known_detections": image["analysis_result"]["known_detections"],
                "unknown_detections": image["analysis_result"]["unknown_detections"],
            }
            for image in images
        ],
        "overlays": overlays,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
