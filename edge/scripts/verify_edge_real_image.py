from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
from scipy.ndimage import binary_closing, binary_opening, label


ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = ROOT / "edge" / "models" / "sonar_ssl_unet.onnx"
IMAGE_PATH = ROOT / "backend" / "test_dataimages" / "images" / "Viator_071.png"
OUTPUT_DIR = ROOT / "edge" / "outputs"
OUTPUT_PATH = OUTPUT_DIR / "Viator_071_onnx_postprocessed.png"


SEGMENTATION_THRESHOLD = 0.80
MINIMUM_AREA_PIXELS = 500


def preprocess(image_path: Path):
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)

    if image is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")

    original_shape = image.shape

    resized = cv2.resize(
        image,
        (512, 512),
        interpolation=cv2.INTER_AREA,
    )

    tensor = resized.astype(np.float32) / 255.0
    tensor = tensor[np.newaxis, np.newaxis, :, :]

    return image, tensor, original_shape


def main():
    print("=" * 60)
    print("EDGE ONNX - BACKEND-CONSISTENT POST-PROCESSING")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

    if not IMAGE_PATH.exists():
        raise FileNotFoundError(f"Image not found: {IMAGE_PATH}")

    session = ort.InferenceSession(
        str(MODEL_PATH),
        providers=["CPUExecutionProvider"],
    )

    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name

    original_image, tensor, original_shape = preprocess(IMAGE_PATH)

    output = session.run(
        [output_name],
        {input_name: tensor},
    )[0]

    probabilities = 1.0 / (1.0 + np.exp(-output[0, 0]))

    # Initial segmentation mask.
    raw_mask = probabilities >= SEGMENTATION_THRESHOLD

    # Same morphology used by backend candidate discovery.
    cleaned_mask = binary_opening(
        raw_mask,
        iterations=1,
    )

    cleaned_mask = binary_closing(
        cleaned_mask,
        iterations=2,
    )

    # Connected-component analysis.
    labeled, component_count = label(cleaned_mask)

    components = []

    for component_id in range(1, component_count + 1):

        pixels = np.argwhere(labeled == component_id)

        area_pixels = len(pixels)

        if area_pixels < MINIMUM_AREA_PIXELS:
            continue

        ymin, xmin = pixels.min(axis=0)
        ymax, xmax = pixels.max(axis=0)

        components.append(
            {
                "area": area_pixels,
                "bbox": [
                    int(xmin),
                    int(ymin),
                    int(xmax),
                    int(ymax),
                ],
            }
        )

    # Resize cleaned mask back to original image size.
    mask_512 = (
        cleaned_mask.astype(np.uint8) * 255
    )

    mask = cv2.resize(
        mask_512,
        (original_shape[1], original_shape[0]),
        interpolation=cv2.INTER_NEAREST,
    )

    # Create visualization.
    base = cv2.cvtColor(
        original_image,
        cv2.COLOR_GRAY2BGR,
    )

    overlay = base.copy()

    overlay[mask > 0] = (0, 0, 255)

    result = cv2.addWeighted(
        base,
        0.70,
        overlay,
        0.30,
        0,
    )

    # Draw component bounding boxes.
    scale_x = original_shape[1] / 512.0
    scale_y = original_shape[0] / 512.0

    for index, component in enumerate(
        sorted(
            components,
            key=lambda x: x["area"],
            reverse=True,
        ),
        start=1,
    ):

        xmin, ymin, xmax, ymax = component["bbox"]

        xmin = int(xmin * scale_x)
        xmax = int(xmax * scale_x)
        ymin = int(ymin * scale_y)
        ymax = int(ymax * scale_y)

        cv2.rectangle(
            result,
            (xmin, ymin),
            (xmax, ymax),
            (0, 255, 255),
            4,
        )

        cv2.putText(
            result,
            f"shipwreck_{index:03d}",
            (xmin + 5, max(20, ymin - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )

    cv2.imwrite(
        str(OUTPUT_PATH),
        result,
    )

    raw_pixels = int(raw_mask.sum())
    cleaned_pixels = int(cleaned_mask.sum())

    print(f"Input shape:              {tensor.shape}")
    print(f"Original image:           {original_shape}")
    print(f"Threshold:                {SEGMENTATION_THRESHOLD}")
    print(f"Raw positive pixels:      {raw_pixels}")
    print(f"Cleaned positive pixels:  {cleaned_pixels}")
    print(f"Raw components:            {component_count}")
    print(f"Valid components:          {len(components)}")
    print(f"Minimum area:              {MINIMUM_AREA_PIXELS}")
    print()
    print("Detected components:")

    for index, component in enumerate(
        sorted(
            components,
            key=lambda x: x["area"],
            reverse=True,
        ),
        start=1,
    ):
        print(
            f"  shipwreck_{index:03d}: "
            f"area={component['area']} "
            f"bbox={component['bbox']}"
        )

    print()
    print("Output:")
    print(OUTPUT_PATH)

    print()
    print("=" * 60)
    print("EDGE POST-PROCESSING: SUCCESS")
    print("=" * 60)


if __name__ == "__main__":
    main()