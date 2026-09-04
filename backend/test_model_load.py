import os
import sys
from pathlib import Path
import torch

# Ensure backend root is on sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.models.ssl_unet import SSLUNet

def test_loading():
    weights_path = BASE_DIR / "app" / "weights" / "best_ssl_unet_accuracy.pth"
    if not weights_path.exists():
        # Fallback to root relative path if needed
        weights_path = Path("backend/app/weights/best_ssl_unet_accuracy.pth")

    print(f"Loading checkpoint from {weights_path}...")
    checkpoint = torch.load(weights_path, map_location="cpu")
    state_dict = checkpoint.get("model_state_dict", checkpoint)

    model = SSLUNet(in_channels=1, num_classes=1)
    
    # Load with strict=True
    load_result = model.load_state_dict(state_dict, strict=True)
    missing = load_result.missing_keys
    unexpected = load_result.unexpected_keys

    print(f"MISSING KEYS COUNT: {len(missing)}")
    print(f"UNEXPECTED KEYS COUNT: {len(unexpected)}")
    
    if len(missing) > 0:
        print("Missing keys:", missing)
    if len(unexpected) > 0:
        print("Unexpected keys:", unexpected)

    model.eval()

    # Inference test with dummy tensor [1, 1, 512, 512]
    dummy_input = torch.randn(1, 1, 512, 512)
    with torch.no_grad():
        logits = model(dummy_input)
        prob_mask = torch.sigmoid(logits)
        binary_mask = (prob_mask > 0.5).float()

    print(f"INPUT SHAPE: {list(dummy_input.shape)}")
    print(f"OUTPUT LOGITS SHAPE: {list(logits.shape)}")
    print(f"PROBABILITY MASK SHAPE: {list(prob_mask.shape)}")
    print(f"BINARY MASK SHAPE: {list(binary_mask.shape)}")
    print(f"Probabilities Min: {prob_mask.min().item():.4f}, Max: {prob_mask.max().item():.4f}")

if __name__ == "__main__":
    test_loading()
