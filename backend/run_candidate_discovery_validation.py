"""Validate experimental candidate discovery on one positive and one negative SSS image."""

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import label

from app.config import OUTPUTS_DIR, SEGMENTATION_THRESHOLD
from app.services.candidate_discovery import CandidateDiscoveryConfig, ExperimentalCandidateDiscovery
from app.services.pytorch_provider import PyTorchInferenceProvider


BACKEND_DIR = Path(__file__).resolve().parent
DATA_DIR = BACKEND_DIR / "test_dataimages"
OUTPUT_DIR = OUTPUTS_DIR / "experimental_candidate_discovery_validation"
CASES = {
    "Viator_07": {
        "image": DATA_DIR / "images" / "Viator_071.png",
        "ground_truth": DATA_DIR / "ground_truth" / "Viator_07.png",
    },
    "Monohansett_01": {
        "image": DATA_DIR / "images" / "Monohansett_01.png",
        "ground_truth": DATA_DIR / "ground_truth" / "Monohansett_01.png",
    },
}


def overlap_percentage(candidate_mask: np.ndarray, reference_mask: np.ndarray) -> float:
    candidate_pixels = int(candidate_mask.sum())
    if candidate_pixels == 0:
        return 0.0
    return round(float(np.logical_and(candidate_mask, reference_mask).sum()) / candidate_pixels * 100.0, 6)


def component_masks(candidate_mask: np.ndarray, candidates: list[dict]) -> list[np.ndarray]:
    labeled, component_count = label(candidate_mask)
    components = []
    for component_id in range(1, component_count + 1):
        mask = labeled == component_id
        area = int(mask.sum())
        if area >= 500:
            components.append(mask)
    components.sort(key=lambda mask: int(mask.sum()), reverse=True)
    if len(components) != len(candidates):
        raise AssertionError("Candidate component count does not match discovery output")
    return components


def panel_image(title: str, image: Image.Image, width: int = 420) -> Image.Image:
    height = max(1, round(width * image.height / image.width))
    resized = image.convert("RGB").resize((width, height), Image.Resampling.LANCZOS)
    panel = Image.new("RGB", (width, height + 38), (15, 20, 35))
    panel.paste(resized, (0, 38))
    ImageDraw.Draw(panel).text((10, 13), title, fill=(0, 245, 212), font=ImageFont.load_default())
    return panel


def save_comparison(
    case_name: str,
    original: Image.Image,
    ground_truth: np.ndarray,
    probability_map: np.ndarray,
    candidate_mask: np.ndarray,
    output_path: Path,
) -> None:
    original_panel = panel_image("Original", original)
    ground_truth_panel = panel_image("Ground Truth", Image.fromarray((ground_truth.astype(np.uint8) * 255), mode="L"))
    probability_panel = panel_image("U-Net probability / mask", Image.fromarray(np.clip(probability_map * 255, 0, 255).astype(np.uint8), mode="L"))

    candidate_overlay = original.convert("RGBA")
    candidate_layer = Image.new("RGBA", original.size, (255, 150, 0, 0))
    candidate_layer.putalpha(Image.fromarray((candidate_mask.astype(np.uint8) * 150), mode="L"))
    candidate_overlay = Image.alpha_composite(candidate_overlay, candidate_layer).convert("RGB")
    candidate_panel = panel_image("Candidate Discovery", candidate_overlay)

    width = original_panel.width
    height = original_panel.height
    comparison = Image.new("RGB", (width * 2, height * 2), (15, 20, 35))
    comparison.paste(original_panel, (0, 0))
    comparison.paste(ground_truth_panel, (width, 0))
    comparison.paste(probability_panel, (0, height))
    comparison.paste(candidate_panel, (width, height))
    draw = ImageDraw.Draw(comparison)
    draw.text((12, comparison.height - 18), case_name, fill=(255, 255, 0), font=ImageFont.load_default())
    comparison.save(output_path, format="PNG")


def save_four_panel(
    case_name: str,
    original: Image.Image,
    maps: dict[str, np.ndarray],
    output_path: Path,
) -> None:
    panels = [
        panel_image("Original SSS", original),
        panel_image("U-Net shipwreck mask", Image.fromarray((maps["shipwreck_mask"].astype(np.uint8) * 255), mode="L")),
        panel_image("Combined candidate score", Image.fromarray(np.clip(maps["candidate_score"] * 255, 0, 255).astype(np.uint8), mode="L")),
        panel_image("FINAL candidate overlay", Image.open(output_path.parent / case_name / "06_candidate_regions_overlay.png")),
    ]
    width = panels[0].width
    height = panels[0].height
    comparison = Image.new("RGB", (width * 2, height * 2), (15, 20, 35))
    for index, panel in enumerate(panels):
        comparison.paste(panel, ((index % 2) * width, (index // 2) * height))
    ImageDraw.Draw(comparison).text((12, comparison.height - 18), case_name, fill=(255, 255, 0), font=ImageFont.load_default())
    comparison.save(output_path, format="PNG")


def main() -> None:
    provider = PyTorchInferenceProvider()
    config = CandidateDiscoveryConfig(
        contrast_weight=0.5,
        ssl_novelty_weight=0.5,
        candidate_score_threshold=0.65,
    )
    discovery = ExperimentalCandidateDiscovery(provider=provider, config=config)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "experimental": True,
        "configuration": {
            "contrast_weight": config.contrast_weight,
            "ssl_novelty_weight": config.ssl_novelty_weight,
            "candidate_score_threshold": config.candidate_score_threshold,
            "minimum_area_pixels": config.minimum_area_pixels,
            "background_percentile": config.background_percentile,
            "morphology": "binary opening iterations=1, binary closing iterations=2",
            "shipwreck_mask_threshold": SEGMENTATION_THRESHOLD,
        },
        "overlap_definition": "intersection(candidate region, reference mask) / candidate region pixels * 100",
        "cases": {},
    }

    for case_name, paths in CASES.items():
        result = discovery.discover(paths["image"], OUTPUT_DIR / case_name)
        with Image.open(paths["ground_truth"]) as ground_truth_image:
            ground_truth = np.asarray(ground_truth_image.convert("L")) > 0
        evidence = discovery._load_evidence(paths["image"])
        maps = discovery._build_maps(evidence)
        candidate_mask = maps["candidate_mask"]
        predicted_mask = maps["shipwreck_mask"]
        exact_candidate_masks = component_masks(candidate_mask, result["candidates"])

        for candidate, component_mask in zip(result["candidates"], exact_candidate_masks):
            candidate["ground_truth_overlap_percentage"] = overlap_percentage(component_mask, ground_truth)
            candidate["unet_predicted_mask_overlap_percentage"] = overlap_percentage(component_mask, predicted_mask)

        save_comparison(
            case_name,
            evidence["original_rgb"],
            ground_truth,
            evidence["probability_map"],
            candidate_mask,
            OUTPUT_DIR / f"{case_name}_comparison.png",
        )
        four_panel_path = OUTPUT_DIR / f"{case_name}_four_panel.png"
        save_four_panel(
            case_name,
            evidence["original_rgb"],
            maps,
            four_panel_path,
        )
        result["ground_truth_positive_pixels"] = int(ground_truth.sum())
        result["candidate_ground_truth_overlap_percentage"] = overlap_percentage(candidate_mask, ground_truth)
        result["candidate_unet_predicted_mask_overlap_percentage"] = overlap_percentage(candidate_mask, predicted_mask)
        result["final_candidate_overlay"] = str(OUTPUT_DIR / case_name / "06_candidate_regions_overlay.png")
        result["comparison_visualization"] = str(OUTPUT_DIR / f"{case_name}_comparison.png")
        result["four_panel_visualization"] = str(four_panel_path)
        report["cases"][case_name] = result

    report_path = OUTPUT_DIR / "validation_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"report: {report_path}")


if __name__ == "__main__":
    main()
