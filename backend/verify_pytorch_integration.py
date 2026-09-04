import torch
from pathlib import Path
from app.models.ssl_unet import SSLUNet
from app.services.pytorch_provider import PyTorchInferenceProvider

def run_verification():
    weights_path = Path("backend/app/weights/best_ssl_unet_accuracy.pth")
    print(f"MODEL FILE: {weights_path}")
    
    checkpoint = torch.load(weights_path, map_location="cpu")
    state_dict = checkpoint["model_state_dict"]
    print("MODEL ARCHITECTURE: SSLUNet (ResNet18 Backbone Encoder + UNet Decoder)")

    model = SSLUNet(in_channels=1, num_classes=1)
    load_res = model.load_state_dict(state_dict, strict=True)
    
    missing_keys = load_res.missing_keys
    unexpected_keys = load_res.unexpected_keys

    print(f"CHECKPOINT LOADED: True (strict=True)")
    print(f"MISSING KEYS: {len(missing_keys)}")
    print(f"UNEXPECTED KEYS: {len(unexpected_keys)}")

    assert len(missing_keys) == 0, f"Expected 0 missing keys, got {len(missing_keys)}"
    assert len(unexpected_keys) == 0, f"Expected 0 unexpected keys, got {len(unexpected_keys)}"

    model.eval()
    dummy_input = torch.randn(1, 1, 512, 512)
    print(f"INPUT SHAPE: {list(dummy_input.shape)}")

    with torch.no_grad():
        logits = model(dummy_input)
        prob_mask = torch.sigmoid(logits)
        binary_mask = (prob_mask > 0.5).float()

    print(f"OUTPUT SHAPE: {list(logits.shape)}")
    print(f"INFERENCE TEST: PASSED (Probabilities Range [{prob_mask.min().item():.4f}, {prob_mask.max().item():.4f}], Binary Mask Shape {list(binary_mask.shape)})")
    print(f"STATUS: VERIFIED SUCCESS")

    # Also test provider class instantiation
    provider = PyTorchInferenceProvider()
    print(f"PROVIDER NAME: {provider.provider_name}")
    print(f"PROVIDER IS MOCK: {provider.is_mock}")

if __name__ == "__main__":
    run_verification()
