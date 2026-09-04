import unittest
import os
import io
import zipfile
from pathlib import Path
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

class TestSonarBackend(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_01_health(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        # Accept either real PyTorch provider or fallback Mock provider
        self.assertTrue(
            "InferenceProvider" in data["inference_provider"],
            f"Unexpected inference_provider value: {data['inference_provider']}"
        )

    def test_02_list_logs(self):
        res = self.client.get("/api/logs")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1) # pre-seeded demo log

    def test_03_upload_multiple_images(self):
        # Create 3 dummy images in memory
        files = []
        for i in range(1, 4):
            img = Image.new("RGB", (400, 200), color=(10 + i*10, 20, 30))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            files.append(("files", (f"test_sonar_{i:02d}.png", buf.getvalue(), "image/png")))

        res = self.client.post("/api/logs/upload", files=files, data={"log_name": "Test_Survey_Multi"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total_images"], 3)
        self.assertEqual(data["status"], "UPLOADED")
        log_id = data["log_id"]

        # Trigger analysis
        res_an = self.client.post(f"/api/logs/{log_id}/analyze")
        self.assertEqual(res_an.status_code, 200)

        # Status check
        res_st = self.client.get(f"/api/logs/{log_id}/status")
        self.assertEqual(res_st.status_code, 200)
        st_data = res_st.json()
        self.assertEqual(st_data["log_id"], log_id)

    def test_04_upload_zip(self):
        # Create ZIP in memory
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as z:
            for i in range(1, 4):
                img = Image.new("RGB", (300, 300), color=(10, 30 + i*10, 50))
                ibuf = io.BytesIO()
                img.save(ibuf, format="PNG")
                z.writestr(f"survey_folder/sonar_zip_{i:02d}.png", ibuf.getvalue())

        zip_buf.seek(0)
        files = {"zip_file": ("test_survey.zip", zip_buf.getvalue(), "application/zip")}
        res = self.client.post("/api/logs/upload", files=files, data={"log_name": "Test_Survey_ZIP"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total_images"], 3)
        self.assertEqual(data["log_name"], "Test_Survey_ZIP")

if __name__ == "__main__":
    unittest.main()
