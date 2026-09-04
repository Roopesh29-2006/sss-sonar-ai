"""
Threshold Sweep -- SonarAI
==========================
Runs the real SSLUNet checkpoint against a fixed SSS image at multiple thresholds.
Saves one labeled overlay per threshold for visual comparison.
Uses scipy.ndimage for fast connected-component analysis.

Usage:
    python threshold_sweep.py
"""

import sys
import os
from pathlib import Path

# Make backend/app importable
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageDraw, ImageFont

from app.models.ssl_unet import SSLUNet
from app.config import WEIGHTS_DIR, OUTPUTS_DIR

# ─────────────────────────────────────────────────────────────────────────────
# Fast connected-component labelling
# ─────────────────────────────────────────────────────────────────────────────
try:
    from scipy.ndimage import label as scipy_label
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

def find_components(binary_mask: np.ndarray, min_pixels: int = 50):
    """
    Returns list of component dicts sorted by size desc.
    Uses scipy.ndimage.label when available (fast), otherwise
    falls back to a vectorised NumPy approach per bounding-box slice.
    """
    if binary_mask.sum() == 0:
        return []

    if HAS_SCIPY:
        labeled, n_features = scipy_label(binary_mask)
    else:
        # Minimal fallback: treat the entire mask as one component
        labeled = binary_mask.astype(np.int32)
        n_features = 1

    components = []
    for lbl in range(1, n_features + 1):
        pixels = np.argwhere(labeled == lbl)
        if len(pixels) < min_pixels:
            continue
        ymin, xmin = pixels.min(axis=0)
        ymax, xmax = pixels.max(axis=0)
        area_pct = round(len(pixels) / binary_mask.size * 100, 4)
        components.append({
            "pixel_count": len(pixels),
            "ymin": int(ymin), "xmin": int(xmin),
            "ymax": int(ymax), "xmax": int(xmax),
            "area_pct": area_pct,
        })

    components.sort(key=lambda c: c["pixel_count"], reverse=True)
    return components


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────
IMAGE_PATH = Path(
    r"C:\Users\Welcome\OneDrive\Desktop\sonar-detection\backend\app"
    r"\storage\uploads\survey_real_ai4shipwrecks\Monohansett_01.png"
)
SWEEP_THRESHOLDS = [0.30, 0.40, 0.50, 0.60, 0.70, 0.80]
OUTPUT_DIR = OUTPUTS_DIR / "threshold_sweep"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MASK_COLOR   = (0, 245, 212)   # teal  -- mask fill
BOX_COLOR    = (255, 80,  80)  # red   -- bounding boxes
BANNER_BG    = (15, 20, 35)    # dark  -- header background
BANNER_TEXT  = (0, 245, 212)   # teal  -- header text

print(f"[sweep] scipy available: {HAS_SCIPY}")

# ─────────────────────────────────────────────────────────────────────────────
# 1. Load real model
# ─────────────────────────────────────────────────────────────────────────────
weights_path = WEIGHTS_DIR / "best_ssl_unet_accuracy.pth"
print(f"[sweep] Loading checkpoint: {weights_path}")

checkpoint = torch.load(weights_path, map_location="cpu")
state_dict = checkpoint.get("model_state_dict", checkpoint)

model = SSLUNet(in_channels=1, num_classes=1)
load_res = model.load_state_dict(state_dict, strict=True)
assert len(load_res.missing_keys) == 0,    f"Missing keys: {load_res.missing_keys}"
assert len(load_res.unexpected_keys) == 0, f"Unexpected keys: {load_res.unexpected_keys}"
model.eval()
print("[sweep] Checkpoint loaded OK -- missing=0  unexpected=0")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Load + preprocess (identical to pytorch_provider.py)
# ─────────────────────────────────────────────────────────────────────────────
print(f"[sweep] Opening image: {IMAGE_PATH}")
assert IMAGE_PATH.exists(), f"Image not found: {IMAGE_PATH}"

with Image.open(IMAGE_PATH) as raw:
    img_rgb  = raw.convert("RGB")
    img_gray = raw.convert("L")
    w, h = img_rgb.size

print(f"[sweep] Input: {w}x{h} px  ({w*h:,} total pixels)")

img_np     = np.array(img_gray, dtype=np.float32) / 255.0
inp_tensor = torch.from_numpy(img_np).unsqueeze(0).unsqueeze(0)   # [1,1,H,W]

target_h = max(32, (h // 32) * 32)
target_w = max(32, (w // 32) * 32)
if target_h != h or target_w != w:
    inp_resized = F.interpolate(inp_tensor, size=(target_h, target_w),
                                mode="bilinear", align_corners=False)
    print(f"[sweep] Resized for UNet: ({h},{w}) -> ({target_h},{target_w})")
else:
    inp_resized = inp_tensor
    print(f"[sweep] No resize required -- image already aligned to 32px grid")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Single forward pass  (shared probability map)
# ─────────────────────────────────────────────────────────────────────────────
print("[sweep] Running SSLUNet forward pass...")
with torch.no_grad():
    logits      = model(inp_resized)
    prob_up     = torch.sigmoid(logits)
    if target_h != h or target_w != w:
        prob_up = F.interpolate(prob_up, size=(h, w),
                                mode="bilinear", align_corners=False)

prob_np = prob_up.squeeze().cpu().numpy()   # [H, W]  float32 0..1

print(f"[sweep] Probability map: min={prob_np.min():.4f}  "
      f"max={prob_np.max():.4f}  mean={prob_np.mean():.4f}")

# ─────────────────────────────────────────────────────────────────────────────
# 4. Helper: build one overlay image
# ─────────────────────────────────────────────────────────────────────────────
def build_overlay(thresh: float, mask_np: np.ndarray, components: list) -> Image.Image:
    pos_px   = int(mask_np.sum())
    area_pct = pos_px / (h * w) * 100
    n_comp   = len(components)

    # Teal semi-transparent mask layer
    base       = img_rgb.convert("RGBA")
    mask_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    mask_pil   = Image.fromarray((mask_np * 255).astype(np.uint8), mode="L")
    mask_layer.paste((*MASK_COLOR, 110), mask=mask_pil)
    composite  = Image.alpha_composite(base, mask_layer).convert("RGB")

    draw = ImageDraw.Draw(composite)

    # Bounding boxes (skip tiny noise < 200 px)
    for comp in components:
        if comp["pixel_count"] < 200:
            continue
        draw.rectangle(
            [comp["xmin"], comp["ymin"], comp["xmax"], comp["ymax"]],
            outline=BOX_COLOR, width=3
        )
        # Small label above box
        lbl = f"{comp['pixel_count']:,}px"
        draw.text((comp["xmin"] + 4, max(0, comp["ymin"] - 18)),
                  lbl, fill=BOX_COLOR)

    # Header banner
    banner_h   = 64
    banner_img = Image.new("RGB", (w, banner_h), BANNER_BG)
    bd         = ImageDraw.Draw(banner_img)
    try:
        font = ImageFont.truetype("arial.ttf", 22)
    except Exception:
        font = ImageFont.load_default()

    header = (
        f"Threshold: {thresh:.2f}   |   "
        f"Positive px: {pos_px:,}   |   "
        f"Area: {area_pct:.3f}%   |   "
        f"Components: {n_comp}"
    )
    bd.text((20, 20), header, fill=BANNER_TEXT, font=font)

    final = Image.new("RGB", (w, banner_h + h))
    final.paste(banner_img, (0, 0))
    final.paste(composite, (0, banner_h))
    return final


# ─────────────────────────────────────────────────────────────────────────────
# 5. Sweep
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*72)
print(f"  THRESHOLD SWEEP  --  {IMAGE_PATH.name}")
print("="*72)

summary = []

for thresh in SWEEP_THRESHOLDS:
    mask_np    = (prob_np >= thresh).astype(np.uint8)
    pos_px     = int(mask_np.sum())
    area_pct   = round(pos_px / (h * w) * 100, 4)
    components = find_components(mask_np, min_pixels=50)
    n_comp     = len(components)

    print(f"\n  thresh={thresh:.2f}  pos_px={pos_px:,}  area={area_pct:.4f}%  "
          f"components={n_comp}")
    for i, c in enumerate(components[:5], 1):
        bw = c["xmax"] - c["xmin"]
        bh = c["ymax"] - c["ymin"]
        print(f"    [{i}] bbox=({c['xmin']},{c['ymin']})->({c['xmax']},{c['ymax']})  "
              f"size={bw}x{bh}  pixels={c['pixel_count']:,}  area={c['area_pct']:.4f}%")

    out_file = OUTPUT_DIR / f"thresh_{str(thresh).replace('.','_')}.png"
    overlay  = build_overlay(thresh, mask_np, components)
    overlay.save(out_file, format="PNG")
    print(f"    -> Saved: {out_file}")

    summary.append({
        "threshold":  thresh,
        "pos_px":     pos_px,
        "area_pct":   area_pct,
        "n_comp":     n_comp,
        "components": components,
        "out_file":   str(out_file),
    })

# ─────────────────────────────────────────────────────────────────────────────
# 6. Summary table
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*72)
print("  SUMMARY TABLE")
print("="*72)
print(f"  {'Thresh':>8}  {'Pos Pixels':>12}  {'Area %':>9}  "
      f"{'Components':>12}  {'Largest BBox':>18}")
print("  " + "-"*68)
for row in summary:
    comps = row["components"]
    if comps:
        c  = comps[0]
        bb = f"{c['xmax']-c['xmin']}x{c['ymax']-c['ymin']}"
    else:
        bb = "--"
    print(f"  {row['threshold']:>8.2f}  {row['pos_px']:>12,}  "
          f"{row['area_pct']:>9.4f}%  {row['n_comp']:>12}  {bb:>18}")

# ─────────────────────────────────────────────────────────────────────────────
# 7. Recommendation
#    Heuristic: prefer the LOWEST threshold where n_components is still small
#    (1-3 dominant objects) and area is meaningful (>0.05%). Higher thresholds
#    that fragment the mask into many tiny components signal over-thresholding.
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*72)
print("  RECOMMENDATION")
print("="*72)

best = None
best_score = float("inf")

for row in summary:
    n = row["n_comp"]
    a = row["area_pct"]

    if a < 0.02:   # nothing meaningful detected
        continue
    if n == 0:
        continue

    # Lower score = better:
    #   prefer fewer components (less noise fragmentation)
    #   mild penalty for very low area (might be under-detecting)
    #   mild penalty for very high area (might be over-detecting shadow)
    score = (n * 2) + max(0.0, 0.5 - a) * 10 + max(0.0, a - 5.0) * 2
    if score < best_score:
        best_score = score
        best = row

print()
if best:
    comps = best["components"]
    print(f"  *** Recommended threshold: {best['threshold']:.2f}")
    print(f"      Positive pixels : {best['pos_px']:,}  ({best['area_pct']:.4f}% of image)")
    print(f"      Components      : {best['n_comp']}")
    if comps:
        c = comps[0]
        print(f"      Largest BBox    : ({c['xmin']},{c['ymin']}) -> "
              f"({c['xmax']},{c['ymax']})  size={c['xmax']-c['xmin']}x{c['ymax']-c['ymin']}")
    print(f"      Overlay         : {best['out_file']}")
    print()
    print("  NOTE: Production threshold has NOT been changed.")
    print("        To apply, update SEGMENTATION_THRESHOLD in backend/app/config.py")
    print("        and change the threshold value in pytorch_provider.py line 131.")
else:
    print("  Could not determine a clear best threshold.")
    print("  Check the probability map min/max values printed above.")
    print("  The model may not be detecting anything in this image at any threshold.")

print("\n[sweep] Complete. Overlays saved to:")
print(f"  {OUTPUT_DIR}")
print()
