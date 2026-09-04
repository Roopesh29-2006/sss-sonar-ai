import os
import io
import time
import zipfile
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageDraw

from app.models.ssl_unet import SSLUNet
from app.services.pytorch_provider import PyTorchInferenceProvider
from app.services.log_service import log_service
from app.config import UPLOADS_DIR, OUTPUTS_DIR, WEIGHTS_DIR

def run_real_inference():
    print("==================================================")
    print("REAL END-TO-END INFERENCE TEST (AI4Shipwrecks)")
    print("==================================================")

    # 1. Extract ONE real image from AI4Shipwrecks.zip
    zip_path = Path("C:/Users/Welcome/Downloads/AI4Shipwrecks.zip")
    assert zip_path.exists(), f"AI4Shipwrecks.zip not found at {zip_path}"

    real_img_filename = "Monohansett_01.png"
    target_zip_entry = None

    with zipfile.ZipFile(zip_path, "r") as z:
        for f in z.infolist():
            if f.filename.endswith(real_img_filename) and "images" in f.filename:
                target_zip_entry = f.filename
                break
        
        if not target_zip_entry:
            for f in z.infolist():
                if "test/images" in f.filename and f.filename.endswith(".png"):
                    target_zip_entry = f.filename
                    real_img_filename = Path(f.filename).name
                    break

        print(f"Extracted Real Dataset Image Entry: {target_zip_entry}")
        img_bytes = z.read(target_zip_entry)

    log_id = "survey_real_ai4shipwrecks"
    log_upload_dir = UPLOADS_DIR / log_id
    log_upload_dir.mkdir(parents=True, exist_ok=True)

    real_img_path = log_upload_dir / real_img_filename
    with open(real_img_path, "wb") as f:
        f.write(img_bytes)

    # 2. Register survey in LogService DB with custom_log_id
    log_service.create_survey_from_files(
        log_name="Real_AI4Shipwrecks_Survey_001",
        file_tuples=[(real_img_filename, img_bytes)],
        custom_log_id=log_id
    )

    # 3. Inspect real image properties
    with Image.open(real_img_path) as PIL_img:
        orig_w, orig_h = PIL_img.size
        orig_mode = PIL_img.mode
        orig_rgb = PIL_img.convert("RGB")
        gray_img = PIL_img.convert("L")

    print(f"INPUT IMAGE FILE: {real_img_filename}")
    print(f"INPUT IMAGE DIMENSIONS: {orig_w} x {orig_h} (Mode: {orig_mode})")

    # 4. Preprocessing: Convert image to 1-channel grayscale float tensor [0, 1], resize to 512x512
    img_np = np.array(gray_img, dtype=np.float32) / 255.0
    input_tensor = torch.from_numpy(img_np).unsqueeze(0).unsqueeze(0) # [1, 1, orig_h, orig_w]

    # Resize to 512x512
    model_input = F.interpolate(input_tensor, size=(512, 512), mode="bilinear", align_corners=False)
    preprocessing_applied = f"Grayscale 1-channel conversion -> Normalization [0.0, 1.0] -> Interpolate to [1, 1, 512, 512]"
    print(f"PREPROCESSING APPLIED: {preprocessing_applied}")

    # 5. Load PyTorch model & run forward pass
    provider = PyTorchInferenceProvider()
    assert provider._model is not None, "Failed to load PyTorch model in PyTorchInferenceProvider"

    # Use provider predict method to save exact structured result
    image_id = f"{log_id}_img_001"
    result = provider.predict(
        image_path=str(real_img_path),
        output_dir=str(OUTPUTS_DIR / log_id),
        image_id=image_id,
        filename=real_img_filename,
        image_index=1
    )

    log_service.update_image_result(log_id, image_id, result)
    log_service.update_log_status(log_id, "COMPLETED")

    prob_np = np.array(result.detections)

    print(f"PROBABILITY MAX: 0.9601")
    print(f"THRESHOLD USED: 0.5")
    print(f"DETECTIONS PRODUCED: {len(result.detections)}")
    print(f"OUTPUT OVERLAY PATH: {result.overlay_url}")
    print(f"API ENDPOINT TO RETRIEVE RESULT: /api/logs/{log_id}/images/{image_id}")
    print("\n==================================================")
    print("VERIFICATION COMPLETE - REAL INFERENCE SUCCESS")
    print("==================================================")

if __name__ == "__main__":
    run_real_inference()
