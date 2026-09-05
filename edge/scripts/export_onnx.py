import sys
from pathlib import Path

import torch

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

OUTPUT = (
    PROJECT_ROOT
    / "edge"
    / "models"
    / "sonar_ssl_unet.onnx"
)


def main():
    print("=" * 60)
    print("SONAR SSL-U-NET → ONNX EXPORT")
    print("=" * 60)

    print(f"Checkpoint: {CHECKPOINT}")
    print(f"Output:     {OUTPUT}")

    if not CHECKPOINT.exists():
        raise FileNotFoundError(
            f"Model checkpoint not found: {CHECKPOINT}"
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    # Exact architecture used during training
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

    # Dummy input used only for tracing/export.
    # Actual H/W will be dynamic.
    dummy_input = torch.randn(
        1, 1, 512, 512,
        dtype=torch.float32
    )

    print("\nModel loaded successfully.")
    print("Export input shape:", tuple(dummy_input.shape))

    with torch.no_grad():
        pytorch_output = model(dummy_input)

    print(
        "PyTorch output shape:",
        tuple(pytorch_output.shape)
    )

    torch.onnx.export(
        model,
        dummy_input,
        str(OUTPUT),
        export_params=True,
        opset_version=17,
        do_constant_folding=True,
        input_names=["image"],
        output_names=["segmentation_logits"],

        # Allow real sonar images with different H/W.
        dynamic_axes={
            "image": {
                2: "height",
                3: "width",
            },
            "segmentation_logits": {
                2: "height",
                3: "width",
            },
        },

        dynamo=False,
    )

    print("\nONNX export completed.")
    print(f"ONNX model: {OUTPUT}")

    import onnx

    onnx_model = onnx.load(str(OUTPUT))
    onnx.checker.check_model(onnx_model)

    print("ONNX structural validation: PASS")

    print("\n" + "=" * 60)
    print("DYNAMIC ONNX EXPORT SUCCESS")
    print("=" * 60)


if __name__ == "__main__":
    main()
    