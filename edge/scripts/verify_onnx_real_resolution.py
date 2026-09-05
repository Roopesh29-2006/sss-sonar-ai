from pathlib import Path

import numpy as np
import cv2
import onnxruntime as ort


ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = ROOT / "edge" / "models" / "sonar_ssl_unet.onnx"
IMAGE_PATH = ROOT / "backend" / "test_dataimages" / "images" / "Viator_071.png"


def main():
    print("=" * 60)
    print("DYNAMIC ONNX - REAL RESOLUTION TEST")
    print("=" * 60)

    image = cv2.imread(
        str(IMAGE_PATH),
        cv2.IMREAD_GRAYSCALE,
    )

    if image is None:
        raise FileNotFoundError(
            f"Could not read image: {IMAGE_PATH}"
        )

    height, width = image.shape

    # Exact preprocessing used by the backend.
    target_h = max(32, (height // 32) * 32)
    target_w = max(32, (width // 32) * 32)

    if (target_h, target_w) != (height, width):
        model_image = cv2.resize(
            image,
            (target_w, target_h),
            interpolation=cv2.INTER_LINEAR,
        )
    else:
        model_image = image

    tensor = (
        model_image.astype(np.float32) / 255.0
    )

    tensor = tensor[np.newaxis, np.newaxis, :, :]

    print(f"Original image:       {height} x {width}")
    print(f"Backend model input:  {target_h} x {target_w}")
    print(f"Input tensor shape:   {tensor.shape}")

    session = ort.InferenceSession(
        str(MODEL_PATH),
        providers=["CPUExecutionProvider"],
    )

    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name

    output = session.run(
        [output_name],
        {input_name: tensor},
    )[0]

    print(f"ONNX output shape:    {output.shape}")

    expected_shape = (
        1,
        1,
        target_h,
        target_w,
    )

    if output.shape != expected_shape:
        raise RuntimeError(
            f"Unexpected ONNX output shape: {output.shape}"
        )

    # Convert logits to probabilities.
    probabilities = 1.0 / (
        1.0 + np.exp(-output[0, 0])
    )

    # Restore to original image dimensions,
    # exactly like the backend.
    if (target_h, target_w) != (height, width):
        probabilities_original = cv2.resize(
            probabilities,
            (width, height),
            interpolation=cv2.INTER_LINEAR,
        )
    else:
        probabilities_original = probabilities

    print(
        f"Final probability map: "
        f"{probabilities_original.shape}"
    )

    print(
        f"Probability min:       "
        f"{probabilities_original.min():.6f}"
    )

    print(
        f"Probability max:       "
        f"{probabilities_original.max():.6f}"
    )

    print(
        f"Probability mean:      "
        f"{probabilities_original.mean():.6f}"
    )

    threshold = 0.80

    mask = (
        probabilities_original >= threshold
    ).astype(np.uint8)

    positive_pixels = int(mask.sum())
    total_pixels = mask.size

    print(f"Threshold:              {threshold}")
    print(f"Positive pixels:        {positive_pixels}")
    print(
        f"Positive percentage:   "
        f"{positive_pixels / total_pixels * 100:.4f}%"
    )

    print()
    print("=" * 60)
    print("REAL-RESOLUTION DYNAMIC ONNX: SUCCESS")
    print("=" * 60)


if __name__ == "__main__":
    main()