"""Diagnostic for real SSL encoder feature extraction on Viator_07."""

from pathlib import Path

import torch

from app.services.pytorch_provider import PyTorchInferenceProvider


IMAGE_PATH = Path(__file__).resolve().parent / "test_dataimages" / "images" / "Viator_071.png"


def main() -> None:
    provider = PyTorchInferenceProvider()
    result = provider.extract_features(IMAGE_PATH)
    feature_map = result["feature_map"]
    variance = float(feature_map.var().item())

    print(f"input shape: {result['input_shape']}")
    print(f"feature layer: {result['feature_layer']}")
    print(f"feature tensor shape: {result['feature_tensor_shape']}")
    print(f"feature min: {feature_map.min().item():.8f}")
    print(f"feature max: {feature_map.max().item():.8f}")
    print(f"feature mean: {feature_map.mean().item():.8f}")
    print(f"feature standard deviation: {feature_map.std().item():.8f}")
    print(f"feature variance: {variance:.8f}")
    assert variance > 0.0, "Feature tensor has zero variance"


if __name__ == "__main__":
    main()