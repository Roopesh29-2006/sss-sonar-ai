import sys
from pathlib import Path

import numpy as np
import torch
import onnxruntime as ort

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.models.ssl_unet import SSLUNet

CHECKPOINT = (
    PROJECT_ROOT
    / "backend"
    / "app"
    / "weights"
    / "best_ssl_unet_accuracy.pth"
)

ONNX_MODEL = (
    PROJECT_ROOT
    / "edge"
    / "models"
    / "sonar_ssl_unet.onnx"
)


def main():
    print("=" * 60)
    print("PYTORCH vs ONNX VERIFICATION")
    print("=" * 60)

    if not CHECKPOINT.exists():
        raise FileNotFoundError(f"Checkpoint not found: {CHECKPOINT}")

    if not ONNX_MODEL.exists():
        raise FileNotFoundError(f"ONNX model not found: {ONNX_MODEL}")

    # Load exact PyTorch model
    model = SSLUNet()

    checkpoint = torch.load(
        CHECKPOINT,
        map_location="cpu"
    )

    model.load_state_dict(
        checkpoint["model_state_dict"],
        strict=True
    )

    model.eval()

    # Reproducible test input
    torch.manual_seed(42)

    x = torch.randn(
        1, 1, 512, 512,
        dtype=torch.float32
    )

    with torch.no_grad():
        pytorch_output = model(x).numpy()

    # Load ONNX
    session = ort.InferenceSession(
        str(ONNX_MODEL),
        providers=["CPUExecutionProvider"]
    )

    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name

    onnx_output = session.run(
        [output_name],
        {input_name: x.numpy()}
    )[0]

    # Compare
    difference = np.abs(
        pytorch_output - onnx_output
    )

    max_difference = float(difference.max())
    mean_difference = float(difference.mean())

    print("\nPyTorch shape:", pytorch_output.shape)
    print("ONNX shape:   ", onnx_output.shape)

    print("\nMaximum absolute difference:", max_difference)
    print("Mean absolute difference:", mean_difference)

    shape_ok = pytorch_output.shape == onnx_output.shape
    numerical_ok = max_difference < 1e-3

    print("\nShape check:",
          "PASS" if shape_ok else "FAIL")

    print("Numerical check:",
          "PASS" if numerical_ok else "FAIL")

    if not shape_ok or not numerical_ok:
        raise RuntimeError("ONNX verification FAILED.")

    print("\n" + "=" * 60)
    print("ONNX MODEL VERIFIED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    main()
