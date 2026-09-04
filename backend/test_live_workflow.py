import requests
import io
import time
from PIL import Image

BASE_URL = "http://127.0.0.1:8000"

def test_live():
    print("1. Checking API Health...")
    r = requests.get(f"{BASE_URL}/api/health")
    assert r.status_code == 200, f"Health check failed: {r.text}"
    print("Health response:", r.json())

    print("\n2. Creating multi-image survey log upload...")
    files = []
    for i in range(1, 4):
        img = Image.new("RGB", (640, 360), color=(20, 40 + i*20, 60))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        files.append(("files", (f"sonar_track_{i:03d}.png", buf.getvalue(), "image/png")))

    r = requests.post(f"{BASE_URL}/api/logs/upload", files=files, data={"log_name": "Live_Verification_Track_001"})
    assert r.status_code == 200, f"Upload failed: {r.text}"
    log_data = r.json()
    log_id = log_data["log_id"]
    print(f"Created Survey Log '{log_id}' with {log_data['total_images']} images.")

    print(f"\n3. Triggering AI Survey Analysis for '{log_id}'...")
    r = requests.post(f"{BASE_URL}/api/logs/{log_id}/analyze")
    assert r.status_code == 200, f"Analyze trigger failed: {r.text}"

    print("\n4. Polling status until COMPLETED...")
    for _ in range(20):
        r = requests.get(f"{BASE_URL}/api/logs/{log_id}/status")
        st = r.json()
        print(f"Status: {st['status']} | Progress: {st['progress_percent']}% | Processed: {st['processed_images']}/{st['total_images']} | Detections: {st['detections_count']}")
        if st['status'] == 'COMPLETED':
            break
        time.sleep(0.5)

    print("\n5. Fetching survey analysis results...")
    r = requests.get(f"{BASE_URL}/api/logs/{log_id}/results")
    assert r.status_code == 200
    res = r.json()
    print(f"Results: Total Detections = {res['total_detections']} (Known: {res['known_count']}, Unknown: {res['unknown_count']})")

    print("\n6. Fetching single image analysis detail & overlay artifact...")
    r = requests.get(f"{BASE_URL}/api/logs/{log_id}/images")
    imgs = r.json()
    first_img = imgs[0]
    img_detail_res = requests.get(f"{BASE_URL}/api/logs/{log_id}/images/{first_img['image_id']}")
    assert img_detail_res.status_code == 200
    img_detail = img_detail_res.json()
    print("Image detail analysis:", img_detail["analysis_result"]["overlay_url"])

    # Test static file serving of generated overlay
    overlay_url = img_detail["analysis_result"]["overlay_url"]
    static_r = requests.get(f"{BASE_URL}{overlay_url}")
    assert static_r.status_code == 200
    print(f"Static overlay image artifact successfully served ({len(static_r.content)} bytes).")

    print("\nSUCCESS: All SonarAI backend API endpoints and image processing pipelines verified live!")

if __name__ == "__main__":
    test_live()
