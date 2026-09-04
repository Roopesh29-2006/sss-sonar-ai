"""Evaluate real checkpoint predictions against the paired AI4Shipwrecks label."""

import io
import json
import zipfile
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageDraw, ImageFont

from app.config import OUTPUTS_DIR, WEIGHTS_DIR
from app.models.ssl_unet import SSLUNet


BACKEND_DIR = Path(__file__).resolve().parent
IMAGE_PATH = BACKEND_DIR / "test_dataimages" / "images" / "Viator_071.png"
LABEL_PATH = BACKEND_DIR / "test_dataimages" / "ground_truth" / "Viator_07.png"
THRESHOLDS = [0.30, 0.40, 0.50, 0.60, 0.70, 0.80]
OUTPUT_DIR = OUTPUTS_DIR / "viator_07_ground_truth_threshold_eval"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def safe_ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 8) if denominator else 0.0


def load_ground_truth() -> np.ndarray:
    with Image.open(IMAGE_PATH) as dataset_image:
        dataset_size = dataset_image.size
    with Image.open(LABEL_PATH) as label_image:
        label = np.array(label_image.convert("L")) > 0

    if label.shape[::-1] != dataset_size:
        raise ValueError(f"Ground-truth size {label.shape[::-1]} differs from image size {dataset_size}")
    return label


def predict_probability_map() -> tuple[np.ndarray, Image.Image]:
    with Image.open(IMAGE_PATH) as raw_image:
        original = raw_image.convert("L")
        image_array = np.array(original, dtype=np.float32) / 255.0

    height, width = image_array.shape
    input_tensor = torch.from_numpy(image_array).unsqueeze(0).unsqueeze(0)
    target_h = max(32, (height // 32) * 32)
    target_w = max(32, (width // 32) * 32)
    if (target_h, target_w) != (height, width):
        input_tensor = F.interpolate(input_tensor, size=(target_h, target_w), mode="bilinear", align_corners=False)

    checkpoint = torch.load(WEIGHTS_DIR / "best_ssl_unet_accuracy.pth", map_location="cpu")
    state_dict = checkpoint.get("model_state_dict", checkpoint)
    model = SSLUNet(in_channels=1, num_classes=1)
    load_result = model.load_state_dict(state_dict, strict=True)
    if load_result.missing_keys or load_result.unexpected_keys:
        raise ValueError(f"Checkpoint mismatch: missing={load_result.missing_keys}, unexpected={load_result.unexpected_keys}")
    model.eval()

    with torch.no_grad():
        probability = torch.sigmoid(model(input_tensor))
        if (target_h, target_w) != (height, width):
            probability = F.interpolate(probability, size=(height, width), mode="bilinear", align_corners=False)
    return probability.squeeze().numpy(), original


def metrics(prediction: np.ndarray, ground_truth: np.ndarray) -> dict:
    true_positive = int(np.count_nonzero(prediction & ground_truth))
    false_positive = int(np.count_nonzero(prediction & ~ground_truth))
    false_negative = int(np.count_nonzero(~prediction & ground_truth))
    true_negative = int(np.count_nonzero(~prediction & ~ground_truth))
    dice = safe_ratio(2 * true_positive, 2 * true_positive + false_positive + false_negative)
    iou = safe_ratio(true_positive, true_positive + false_positive + false_negative)
    precision = safe_ratio(true_positive, true_positive + false_positive)
    recall = safe_ratio(true_positive, true_positive + false_negative)
    return {
        "threshold": None,
        "TP": true_positive,
        "FP": false_positive,
        "FN": false_negative,
        "TN": true_negative,
        "Dice": dice,
        "IoU": iou,
        "Precision": precision,
        "Recall": recall,
    }


def save_overlay(original: Image.Image, prediction: np.ndarray, threshold: float, output_path: Path) -> None:
    base = original.convert("RGBA")
    mask = Image.fromarray((prediction * 255).astype(np.uint8), mode="L")
    layer = Image.new("RGBA", base.size, (0, 245, 212, 0))
    layer.putalpha(mask.point(lambda value: round(value * 110 / 255)))
    overlay = Image.alpha_composite(base, layer).convert("RGB")
    draw = ImageDraw.Draw(overlay)
    banner_height = 48
    banner = Image.new("RGB", (overlay.width, banner_height), (15, 20, 35))
    banner_draw = ImageDraw.Draw(banner)
    banner_draw.text((12, 16), f"Viator_07 | Threshold: {threshold:.2f} | Predicted positive pixels: {int(prediction.sum()):,}", fill=(0, 245, 212), font=ImageFont.load_default())
    labeled = Image.new("RGB", (overlay.width, overlay.height + banner_height))
    labeled.paste(banner, (0, 0))
    labeled.paste(overlay, (0, banner_height))
    labeled.save(output_path, format="PNG")


def make_comparison(original: Image.Image, ground_truth: np.ndarray, predictions: dict, output_path: Path) -> None:
    panel_width = 360
    panel_height = max(1, round(panel_width * original.height / original.width))
    header_height = 48
    canvas = Image.new("RGB", (panel_width * 2, (panel_height + header_height) * 3), (15, 20, 35))
    font = ImageFont.load_default()
    panels = [("Original image", np.array(original))]
    panels.append(("Ground truth mask", ground_truth.astype(np.uint8) * 255))
    for threshold in [0.50, 0.60, 0.70, 0.80]:
        panels.append((f"Prediction {threshold:.2f}", predictions[threshold].astype(np.uint8) * 255))

    for index, (label, array) in enumerate(panels):
        image = Image.fromarray(array).convert("RGB")
        image = image.resize((panel_width, panel_height), Image.Resampling.LANCZOS)
        x = (index % 2) * panel_width
        y = (index // 2) * (panel_height + header_height)
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((x, y, x + panel_width, y + header_height), fill=(15, 20, 35))
        draw.text((x + 12, y + 16), label, fill=(0, 245, 212), font=font)
        canvas.paste(image, (x, y + header_height))

    canvas.save(output_path, format="PNG")


def main() -> None:
    ground_truth = load_ground_truth()
    probability_map, original = predict_probability_map()
    predictions = {}
    rows = []
    for threshold in THRESHOLDS:
        prediction = probability_map >= threshold
        predictions[threshold] = prediction
        row = metrics(prediction, ground_truth)
        row["threshold"] = threshold
        row["predicted_positive_pixels"] = int(prediction.sum())
        rows.append(row)
        save_overlay(original, prediction, threshold, OUTPUT_DIR / f"viator_07_threshold_{threshold:.2f}.png")

    report = {
        "image": str(IMAGE_PATH),
        "ground_truth_mask": str(LABEL_PATH),
        "image_size": [original.width, original.height],
        "ground_truth_positive_pixels": int(ground_truth.sum()),
        "ground_truth_unique_values": [0, 1] if ground_truth.any() else [0],
        "zero_denominator_convention": "Dice, IoU, precision, and recall are reported as 0.0 when their denominator is zero.",
        "metrics": rows,
        "comparison_visualization": str(OUTPUT_DIR / "comparison.png"),
    }
    (OUTPUT_DIR / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    make_comparison(original, ground_truth, predictions, OUTPUT_DIR / "comparison.png")

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()