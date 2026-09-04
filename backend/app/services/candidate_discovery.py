"""Experimental candidate-region discovery using real SSLUNet evidence."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import binary_closing, binary_opening, gaussian_filter, label

from app.config import SEGMENTATION_THRESHOLD
from app.services.pytorch_provider import PyTorchInferenceProvider


@dataclass(frozen=True)
class CandidateDiscoveryConfig:
    contrast_weight: float = 0.5
    ssl_novelty_weight: float = 0.5
    candidate_score_threshold: float = 0.65
    minimum_area_pixels: int = 500
    background_percentile: float = 30.0
    normalization_low_percentile: float = 1.0
    normalization_high_percentile: float = 99.0


class ExperimentalCandidateDiscovery:
    """Prototype only: produces candidate regions, not unknown-object detections."""

    def __init__(
        self,
        provider: PyTorchInferenceProvider | None = None,
        config: CandidateDiscoveryConfig | None = None,
    ) -> None:
        self.provider = provider or PyTorchInferenceProvider()
        self.config = config or CandidateDiscoveryConfig()

    @staticmethod
    def _normalize(values: np.ndarray, low_percentile: float = 1.0, high_percentile: float = 99.0) -> np.ndarray:
        low, high = np.percentile(values, [low_percentile, high_percentile])
        if high <= low:
            return np.zeros_like(values, dtype=np.float32)
        return np.clip((values - low) / (high - low), 0.0, 1.0).astype(np.float32)

    @staticmethod
    def _colorize(values: np.ndarray) -> Image.Image:
        values_uint8 = np.clip(values * 255.0, 0, 255).astype(np.uint8)
        values_int = values_uint8.astype(np.int16)
        red = values_uint8
        green = np.minimum(values_int * 2, 255).astype(np.uint8)
        blue = (255 - values_int).astype(np.uint8)
        return Image.fromarray(np.stack([red, green, blue], axis=-1), mode="RGB")

    def _load_evidence(self, image_path: str | Path) -> dict[str, Any]:
        if self.provider._model is None:
            raise RuntimeError("Real PyTorch model is not loaded.")

        with Image.open(image_path) as image:
            original_rgb = image.convert("RGB")
            original_gray = image.convert("L")
        gray = np.asarray(original_gray, dtype=np.float32) / 255.0
        height, width = gray.shape
        input_tensor = torch.from_numpy(gray).unsqueeze(0).unsqueeze(0)
        target_h = max(32, (height // 32) * 32)
        target_w = max(32, (width // 32) * 32)
        if (target_h, target_w) != (height, width):
            model_input = F.interpolate(input_tensor, size=(target_h, target_w), mode="bilinear", align_corners=False)
        else:
            model_input = input_tensor

        with torch.no_grad():
            logits = self.provider._model(model_input)
            probability = torch.sigmoid(logits)
            feature_map = self.provider._model.extract_encoder_features(model_input)
            if (target_h, target_w) != (height, width):
                probability = F.interpolate(probability, size=(height, width), mode="bilinear", align_corners=False)

        probability_map = probability.squeeze().cpu().numpy().astype(np.float32)
        feature_array = feature_map.squeeze(0).cpu().numpy().astype(np.float32)
        return {
            "original_rgb": original_rgb,
            "gray": gray,
            "probability_map": probability_map,
            "feature_map": feature_array,
            "input_shape": tuple(model_input.shape),
        }

    def _build_maps(self, evidence: dict[str, Any]) -> dict[str, np.ndarray]:
        gray = evidence["gray"]
        probability_map = evidence["probability_map"]
        feature_array = evidence["feature_map"]

        local_background = gaussian_filter(gray, sigma=15.0)
        contrast_raw = np.abs(gray - local_background)
        contrast_map = self._normalize(
            contrast_raw,
            self.config.normalization_low_percentile,
            self.config.normalization_high_percentile,
        )

        channel_activation = np.linalg.norm(feature_array, axis=0)
        background_limit = np.percentile(channel_activation, self.config.background_percentile)
        background_locations = channel_activation <= background_limit
        if not np.any(background_locations):
            background_locations = np.ones(channel_activation.shape, dtype=bool)
        background_reference = feature_array[:, background_locations].mean(axis=1)
        feature_distance = np.linalg.norm(feature_array - background_reference[:, None, None], axis=0)
        novelty_small = self._normalize(
            feature_distance,
            self.config.normalization_low_percentile,
            self.config.normalization_high_percentile,
        )
        novelty_tensor = torch.from_numpy(novelty_small).unsqueeze(0).unsqueeze(0)
        novelty_map = F.interpolate(
            novelty_tensor,
            size=gray.shape,
            mode="bilinear",
            align_corners=False,
        ).squeeze().numpy().astype(np.float32)
        novelty_map = np.clip(novelty_map, 0.0, 1.0)

        candidate_score = (
            self.config.contrast_weight * contrast_map
            + self.config.ssl_novelty_weight * novelty_map
        )
        candidate_score /= self.config.contrast_weight + self.config.ssl_novelty_weight
        shipwreck_mask = probability_map >= SEGMENTATION_THRESHOLD
        candidate_score = candidate_score.astype(np.float32)
        candidate_score[shipwreck_mask] = 0.0
        raw_candidate_mask = candidate_score >= self.config.candidate_score_threshold
        cleaned_candidate_mask = binary_opening(raw_candidate_mask, iterations=1)
        cleaned_candidate_mask = binary_closing(cleaned_candidate_mask, iterations=2)
        return {
            "shipwreck_mask": shipwreck_mask,
            "contrast_map": contrast_map,
            "novelty_map": novelty_map,
            "candidate_score": candidate_score,
            "raw_candidate_mask": raw_candidate_mask,
            "candidate_mask": cleaned_candidate_mask,
        }

    def _extract_candidates(self, candidate_mask: np.ndarray, candidate_score: np.ndarray) -> tuple[list[dict[str, Any]], int]:
        labeled, component_count = label(candidate_mask)
        candidates = []
        for component_id in range(1, component_count + 1):
            pixels = np.argwhere(labeled == component_id)
            area_pixels = len(pixels)
            if area_pixels < self.config.minimum_area_pixels:
                continue
            ymin, xmin = pixels.min(axis=0)
            ymax, xmax = pixels.max(axis=0)
            candidates.append({
                "object_id": f"candidate_{len(candidates) + 1:03d}",
                "status": "candidate",
                "class_name": "candidate_object",
                "novelty_score": round(float(candidate_score[labeled == component_id].mean()), 6),
                "confidence": None,
                "bbox": [int(xmin), int(ymin), int(xmax), int(ymax)],
                "area_pixels": area_pixels,
                "segmentation": [
                    [int(xmin), int(ymin)],
                    [int(xmax), int(ymin)],
                    [int(xmax), int(ymax)],
                    [int(xmin), int(ymax)],
                ],
            })
        candidates.sort(key=lambda candidate: candidate["area_pixels"], reverse=True)
        for index, candidate in enumerate(candidates, start=1):
            candidate["object_id"] = f"candidate_{index:03d}"
        return candidates, component_count

    def _save_visualizations(self, evidence: dict[str, Any], maps: dict[str, np.ndarray], candidates: list[dict[str, Any]], output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        original = evidence["original_rgb"]
        original.save(output_dir / "01_original_sss.png")

        probability_image = self._colorize(evidence["probability_map"])
        probability_overlay = Image.blend(original, probability_image, 0.55)
        shipwreck_mask = Image.fromarray((maps["shipwreck_mask"].astype(np.uint8) * 90), mode="L")
        shipwreck_layer = Image.new("RGBA", original.size, (255, 0, 0, 0))
        shipwreck_layer.putalpha(shipwreck_mask)
        probability_overlay = Image.alpha_composite(probability_overlay.convert("RGBA"), shipwreck_layer).convert("RGB")
        probability_draw = ImageDraw.Draw(probability_overlay)
        probability_draw.text((12, 12), f"U-Net probability | mask threshold {SEGMENTATION_THRESHOLD:.2f}", fill=(255, 255, 0), font=ImageFont.load_default())
        probability_overlay.save(output_dir / "02_unet_probability_mask.png")

        self._colorize(maps["contrast_map"]).save(output_dir / "03_local_contrast.png")
        self._colorize(maps["novelty_map"]).save(output_dir / "04_ssl_novelty.png")
        self._colorize(maps["candidate_score"]).save(output_dir / "05_combined_candidate_score.png")

        final_overlay = original.convert("RGBA")
        shipwreck_layer = Image.new("RGBA", original.size, (255, 0, 0, 0))
        shipwreck_layer.putalpha(Image.fromarray((maps["shipwreck_mask"].astype(np.uint8) * 90), mode="L"))
        candidate_layer = Image.new("RGBA", original.size, (255, 150, 0, 0))
        candidate_layer.putalpha(Image.fromarray((maps["candidate_mask"].astype(np.uint8) * 140), mode="L"))
        final_overlay = Image.alpha_composite(final_overlay, shipwreck_layer)
        final_overlay = Image.alpha_composite(final_overlay, candidate_layer)
        draw = ImageDraw.Draw(final_overlay)
        draw.text((12, 12), "U-Net shipwreck mask: red | candidates: orange", fill=(255, 255, 0, 255), font=ImageFont.load_default())
        for candidate in candidates:
            xmin, ymin, xmax, ymax = candidate["bbox"]
            draw.rectangle((xmin, ymin, xmax, ymax), outline=(255, 60, 0, 255), width=4)
            draw.text((xmin + 4, max(0, ymin - 16)), f"{candidate['object_id']} | score {candidate['novelty_score']:.3f}", fill=(255, 60, 0, 255), font=ImageFont.load_default())
        final_overlay.convert("RGB").save(output_dir / "06_candidate_regions_overlay.png")

    def discover(self, image_path: str | Path, output_dir: str | Path) -> dict[str, Any]:
        evidence = self._load_evidence(image_path)
        maps = self._build_maps(evidence)
        candidates, components_before_filtering = self._extract_candidates(maps["candidate_mask"], maps["candidate_score"])
        self._save_visualizations(evidence, maps, candidates, Path(output_dir))
        candidate_pixels = int(maps["candidate_mask"].sum())
        total_pixels = int(maps["candidate_mask"].size)
        return {
            "experimental": True,
            "image": str(image_path),
            "feature_layer": "encoder.layer4 (e4), before dec4",
            "feature_tensor_shape": [1, *evidence["feature_map"].shape],
            "input_shape": list(evidence["input_shape"]),
            "weights_unchanged": True,
            "segmentation_threshold_unchanged": SEGMENTATION_THRESHOLD,
            "contrast_weight": self.config.contrast_weight,
            "ssl_novelty_weight": self.config.ssl_novelty_weight,
            "candidate_score_is_probability": False,
            "candidate_score_threshold": self.config.candidate_score_threshold,
            "number_candidates_before_filtering": components_before_filtering,
            "number_candidates_after_filtering": len(candidates),
            "candidate_areas": [candidate["area_pixels"] for candidate in candidates],
            "candidate_bounding_boxes": [candidate["bbox"] for candidate in candidates],
            "candidate_scores": [candidate["novelty_score"] for candidate in candidates],
            "candidate_pixels": candidate_pixels,
            "candidate_percentage": round(candidate_pixels / total_pixels * 100.0, 6),
            "candidates": candidates,
            "visualizations": [
                "01_original_sss.png",
                "02_unet_probability_mask.png",
                "03_local_contrast.png",
                "04_ssl_novelty.png",
                "05_combined_candidate_score.png",
                "06_candidate_regions_overlay.png",
            ],
        }
