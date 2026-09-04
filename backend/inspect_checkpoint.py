import torch
from pathlib import Path

weights_path = Path("backend/app/weights/best_ssl_unet_accuracy.pth")
checkpoint = torch.load(weights_path, map_location="cpu")
state_dict = checkpoint["model_state_dict"]

print("--- ALL KEYS AND SHAPES ---")
for k, v in state_dict.items():
    print(f"{k}: {tuple(v.shape)}")
