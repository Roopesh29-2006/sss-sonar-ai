from pathlib import Path
import argparse
import time

import cv2
import numpy as np
import onnxruntime as ort


ROOT = Path(__file__).resolve().parents[2]

DEFAULT_MODEL = (
    ROOT / "edge" / "models" / "sonar_ssl_unet.onnx"
)

SEGMENTATION_THRESHOLD = 0.80


class SonarInference:
    """
    Lightweight ONNX Runtime inference for Raspberry Pi.

    Input:
        Side-scan sonar image.

    Output:
        Shipwreck segmentation mask,
        bounding box,
        model-derived confidence,
        processing time.
    """

    def __init__(
        self,
        model_path: str | Path = DEFAULT_MODEL,
        threshold: float = SEGMENTATION_THRESHOLD,
    ):
        self.model_path = Path(model_path)
        self.threshold = threshold

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"ONNX model not found: {self.model_path}"
            )

        self.session = ort.InferenceSession(
            str(self.model_path),
            providers=["CPUExecutionProvider"],
        )

        self.input_name = (
            self.session.get_inputs()[0].name
        )

        self.output_name = (
            self.session.get_outputs()[0].name
        )

    @staticmethod
    def _prepare_image(image_path: str | Path):
        image_path = Path(image_path)

        image = cv2.imread(
            str(image_path),
            cv2.IMREAD_GRAYSCALE,
        )

        if image is None:
            raise ValueError(
                f"Unable to read sonar image: {image_path}"
            )

        original_height, original_width = image.shape

        # Match backend preprocessing:
        # dimensions are reduced to the nearest multiple of 32.
        target_height = max(
            32,
            (original_height // 32) * 32,
        )

        target_width = max(
            32,
            (original_width // 32) * 32,
        )

        if (
            target_height != original_height
            or target_width != original_width
        ):
            model_image = cv2.resize(
                image,
                (target_width, target_height),
                interpolation=cv2.INTER_LINEAR,
            )
        else:
            model_image = image

        tensor = (
            model_image.astype(np.float32) / 255.0
        )

        tensor = tensor[
            np.newaxis,
            np.newaxis,
            :,
            :,
        ]

        return (
            image,
            tensor,
            original_height,
            original_width,
            target_height,
            target_width,
        )

    def predict(self, image_path: str | Path):
        start_time = time.perf_counter()

        (
            original_image,
            tensor,
            original_height,
            original_width,
            target_height,
            target_width,
        ) = self._prepare_image(image_path)

        output = self.session.run(
            [self.output_name],
            {self.input_name: tensor},
        )[0]

        logits = output[0, 0]

        # Sigmoid.
        probabilities = 1.0 / (
            1.0 + np.exp(-logits)
        )

        # Restore probability map to original resolution.
        if (
            target_height != original_height
            or target_width != original_width
        ):
            probabilities = cv2.resize(
                probabilities,
                (original_width, original_height),
                interpolation=cv2.INTER_LINEAR,
            )

        mask = (
            probabilities >= self.threshold
        ).astype(np.uint8)

        positive_pixels = np.argwhere(mask > 0)

        detections = []

        # Match backend known-detection rule:
        # register an object when >50 positive pixels exist.
        if len(positive_pixels) > 50:

            ymin, xmin = positive_pixels.min(
                axis=0
            )

            ymax, xmax = positive_pixels.max(
                axis=0
            )

            mask_values = probabilities[
                mask > 0
            ]

            confidence = float(
                mask_values.mean()
            )

            # Same confidence bounding behavior
            # used by the backend.
            confidence = round(
                min(
                    max(confidence, 0.50),
                    0.99,
                ),
                3,
            )

            detections.append(
                {
                    "object_id": "det_001",
                    "class_name": "shipwreck",
                    "status": "known",
                    "confidence": confidence,
                    "novelty_score": None,
                    "bbox": [
                        int(xmin),
                        int(ymin),
                        int(xmax),
                        int(ymax),
                    ],
                    "area_pixels": int(
                        mask.sum()
                    ),
                }
            )

        processing_time_ms = round(
            (time.perf_counter() - start_time)
            * 1000,
            2,
        )

        return {
            "image": str(image_path),
            "original_width": original_width,
            "original_height": original_height,
            "model_input": [
                target_height,
                target_width,
            ],
            "threshold": self.threshold,
            "positive_pixels": int(mask.sum()),
            "detections": detections,
            "processing_time_ms": processing_time_ms,
            "mask": mask,
            "probabilities": probabilities,
            "original_image": original_image,
        }


def main():
    parser = argparse.ArgumentParser(
        description="Run lightweight sonar inference with ONNX Runtime."
    )

    parser.add_argument(
        "image",
        help="Path to a side-scan sonar image.",
    )

    parser.add_argument(
        "--model",
        default=str(DEFAULT_MODEL),
        help="Path to ONNX model.",
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=SEGMENTATION_THRESHOLD,
        help="Segmentation threshold.",
    )

    args = parser.parse_args()

    engine = SonarInference(
        model_path=args.model,
        threshold=args.threshold,
    )

    result = engine.predict(args.image)

    print("=" * 60)
    print("SONAR EDGE INFERENCE")
    print("=" * 60)

    print(f"Image:              {result['image']}")
    print(
        f"Original resolution: "
        f"{result['original_width']} x "
        f"{result['original_height']}"
    )

    print(
        f"Model input:        "
        f"{result['model_input'][1]} x "
        f"{result['model_input'][0]}"
    )

    print(
        f"Threshold:          "
        f"{result['threshold']}"
    )

    print(
        f"Positive pixels:    "
        f"{result['positive_pixels']}"
    )

    print(
        f"Detections:         "
        f"{len(result['detections'])}"
    )

    for detection in result["detections"]:
        print()
        print(
            f"  {detection['object_id']}"
        )
        print(
            f"  Class:       "
            f"{detection['class_name']}"
        )
        print(
            f"  Confidence:  "
            f"{detection['confidence']}"
        )
        print(
            f"  BBox:        "
            f"{detection['bbox']}"
        )
        print(
            f"  Area:        "
            f"{detection['area_pixels']}"
        )

    print()
    print(
        f"Processing time:    "
        f"{result['processing_time_ms']} ms"
    )

    print()
    print("=" * 60)
    print("EDGE INFERENCE SUCCESS")
    print("=" * 60)


if __name__ == "__main__":
    main()