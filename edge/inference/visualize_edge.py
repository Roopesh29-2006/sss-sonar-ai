from pathlib import Path
import sys

import cv2
import numpy as np

from sonar_inference import SonarInference


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "edge" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def create_overlay(image_path: str):
    engine = SonarInference()
    result = engine.predict(image_path)

    image = result["original_image"].copy()
    mask = result["mask"]

    # Convert grayscale sonar image to BGR
    overlay = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    # Segmentation overlay
    segmentation = np.zeros_like(overlay)
    segmentation[:, :, 1] = 255  # Green

    alpha = 0.30
    mask_bool = mask > 0

    overlay[mask_bool] = (
        (1 - alpha) * overlay[mask_bool]
        + alpha * segmentation[mask_bool]
    ).astype(np.uint8)

    # Draw detections
    for detection in result["detections"]:
        xmin, ymin, xmax, ymax = detection["bbox"]
        confidence = detection["confidence"]

        # Bounding box
        cv2.rectangle(
            overlay,
            (xmin, ymin),
            (xmax, ymax),
            (255, 255, 0),
            4
        )

        # Contour
        contours, _ = cv2.findContours(
            mask.astype(np.uint8),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        cv2.drawContours(
            overlay,
            contours,
            -1,
            (0, 255, 255),
            3
        )

        # Label
        label = f"SHIPWRECK | Confidence: {confidence:.3f}"

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.2
        thickness = 3

        (text_width, text_height), baseline = cv2.getTextSize(
            label,
            font,
            font_scale,
            thickness
        )

        text_x = xmin
        text_y = max(ymin - 15, text_height + 15)

        # Background for text
        cv2.rectangle(
            overlay,
            (text_x, text_y - text_height - baseline),
            (text_x + text_width + 10, text_y + 5),
            (0, 0, 0),
            -1
        )

        cv2.putText(
            overlay,
            label,
            (text_x + 5, text_y),
            font,
            font_scale,
            (255, 255, 255),
            thickness,
            cv2.LINE_AA
        )

    output_path = OUTPUT_DIR / f"{Path(image_path).stem}_edge_overlay.png"

    cv2.imwrite(str(output_path), overlay)

    print("=" * 60)
    print("EDGE VISUALIZATION")
    print("=" * 60)
    print(f"Input:       {image_path}")
    print(f"Output:      {output_path}")
    print(f"Detections:  {len(result['detections'])}")

    for detection in result["detections"]:
        print(
            f"  {detection['class_name']} | "
            f"confidence={detection['confidence']}"
        )

    print("=" * 60)
    print("EDGE VISUALIZATION SUCCESS")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(
            "Usage: python visualize_edge.py "
            "<path_to_sonar_image>"
        )
        sys.exit(1)

    create_overlay(sys.argv[1])