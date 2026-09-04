import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "app" / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
OUTPUTS_DIR = STORAGE_DIR / "outputs"
WEIGHTS_DIR = BASE_DIR / "app" / "weights"

# Metadata persistence file
DATA_FILE = STORAGE_DIR / "survey_logs_db.json"

# Allowed extensions
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}

# Segmentation threshold — selected from real AI4Shipwrecks ground-truth evaluation.
# Threshold 0.80 produced the best Dice, IoU, and precision with the fewest false positives.
SEGMENTATION_THRESHOLD = 0.80

# Ensure directories exist
for directory in [STORAGE_DIR, UPLOADS_DIR, OUTPUTS_DIR, WEIGHTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
