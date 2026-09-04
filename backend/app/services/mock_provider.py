import hashlib
import time
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from app.models.inference import InferenceProvider
from app.schemas.detection import (
    ImageAnalysisResult,
    DetectionItem,
    BoundingBox,
    SegmentationArea,
    SSLFeatures,
)

class MockInferenceProvider(InferenceProvider):
    """
    Mock Inference Provider for Side-Scan Sonar (SSS) survey analysis.
    Generates realistic, deterministic mock segmentation masks, bounding boxes,
    novelty scores, and SSL feature representations labeled clearly as DEMO/MOCK.
    """

    @property
    def provider_name(self) -> str:
        return "MockInferenceProvider (DEMO)"

    @property
    def is_mock(self) -> bool:
        return True

    def load_model(self) -> bool:
        return True

    def _seed_from_str(self, text: str) -> int:
        h = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return int(h[:8], 16)

    def predict(
        self,
        image_path: str,
        output_dir: str,
        image_id: str,
        filename: str,
        image_index: int,
        latitude: float | None = None,
        longitude: float | None = None,
        location_note: str = "Location data unavailable"
    ) -> ImageAnalysisResult:
        start_time = time.time()
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        log_id = out_path.name

        # 1. Open original sonar image
        try:
            with Image.open(image_path) as img:
                img_conv = img.convert("RGB")
                w, h = img_conv.size
        except Exception:
            w, h = 800, 400
            img_conv = Image.new("RGB", (w, h), color=(20, 30, 45))

        seed = self._seed_from_str(f"{filename}_{image_index}_{w}_{h}")
        rng = np.random.RandomState(seed)

        has_detection = (seed % 100) < 65
        detections = []

        mask_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        overlay_img = img_conv.copy().convert("RGBA")
        draw_mask = ImageDraw.Draw(mask_img)
        draw_overlay = ImageDraw.Draw(overlay_img)

        if has_detection:
            num_obj = 1 if (seed % 100) < 50 else 2
            for obj_idx in range(num_obj):
                obj_seed = seed + obj_idx * 1000
                obj_rng = np.random.RandomState(obj_seed)

                is_shipwreck = (obj_rng.rand() < 0.75)
                cls_name = "shipwreck" if is_shipwreck else "unknown_object"

                bw = int(w * obj_rng.uniform(0.15, 0.35))
                bh = int(h * obj_rng.uniform(0.20, 0.45))
                max_x = max(10, w - bw - 10)
                max_y = max(10, h - bh - 10)
                xmin = float(obj_rng.randint(10, max_x))
                ymin = float(obj_rng.randint(10, max_y))
                xmax = min(float(w - 10), xmin + bw)
                ymax = min(float(h - 10), ymin + bh)

                cx = (xmin + xmax) / 2.0
                cy = (ymin + ymax) / 2.0
                rx = (xmax - xmin) / 2.0
                ry = (ymax - ymin) / 2.0

                num_points = obj_rng.randint(8, 14)
                contour = []
                for p in range(num_points):
                    angle = (2 * math.pi * p) / num_points
                    r_factor = obj_rng.uniform(0.6, 1.0)
                    px = cx + rx * math.cos(angle) * r_factor
                    py = cy + ry * math.sin(angle) * r_factor
                    contour.append([round(px, 1), round(py, 1)])

                if is_shipwreck:
                    confidence = round(float(obj_rng.uniform(0.82, 0.98)), 3)
                    novelty = None
                    status = "known"
                    mask_color = (0, 245, 212, 120)
                    box_color = (0, 245, 212, 255)
                else:
                    confidence = None
                    novelty = round(float(obj_rng.uniform(0.70, 0.95)), 3)
                    status = "unknown"
                    mask_color = (255, 183, 3, 130)
                    box_color = (255, 183, 3, 255)

                poly_tuple = [tuple(pt) for pt in contour]
                draw_mask.polygon(poly_tuple, fill=mask_color, outline=box_color)

                draw_overlay.polygon(poly_tuple, fill=mask_color)
                draw_overlay.rectangle([xmin, ymin, xmax, ymax], outline=box_color, width=3)

                label_text = f"[DEMO] {'Shipwreck' if is_shipwreck else 'UNKNOWN'}"
                draw_overlay.text((xmin + 4, max(0, ymin - 16)), label_text, fill=box_color)

                pixel_area = int((xmax - xmin) * (ymax - ymin) * 0.65)

                det_item = DetectionItem(
                    object_id=f"obj_{image_index}_{obj_idx+1}",
                    class_name=cls_name,
                    status=status,
                    confidence=confidence,
                    novelty_score=novelty,
                    bbox=BoundingBox(xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax),
                    segmentation=SegmentationArea(
                        pixel_count=pixel_area,
                        contour_points=contour
                    ),
                    is_mock=True
                )
                detections.append(det_item)

        final_overlay = Image.alpha_composite(img_conv.convert("RGBA"), mask_img)
        if detections:
            draw_final = ImageDraw.Draw(final_overlay)
            for d in detections:
                box_c = (0, 245, 212, 255) if d.status == "known" else (255, 183, 3, 255)
                draw_final.rectangle([d.bbox.xmin, d.bbox.ymin, d.bbox.xmax, d.bbox.ymax], outline=box_c, width=3)

        mask_file = out_path / f"{image_id}_mask.png"
        overlay_file = out_path / f"{image_id}_overlay.png"
        thumb_file = out_path / f"{image_id}_thumb.jpg"

        mask_img.save(mask_file, format="PNG")
        final_overlay.convert("RGB").save(overlay_file, format="PNG")

        thumb_img = img_conv.copy()
        thumb_img.thumbnail((320, 240))
        thumb_img.save(thumb_file, format="JPEG", quality=85)

        feature_vec = []
        for i in range(128):
            val = math.sin(i * 0.15 + seed) * 0.5 + rng.normal(0, 0.1)
            feature_vec.append(round(float(val), 4))

        sim_score = round(float(rng.uniform(0.72, 0.96)), 3)
        novelty_scores = [d.novelty_score for d in detections if d.novelty_score is not None]
        top_novelty = max(novelty_scores) if novelty_scores else round(float(rng.uniform(0.02, 0.18)), 3)

        ssl_feats = SSLFeatures(
            feature_vector=feature_vec,
            similarity_score=sim_score,
            novelty_score=top_novelty,
            is_mock=True
        )

        proc_time = round((time.time() - start_time) * 1000 + rng.uniform(40, 90), 1)
        known_detections = [d for d in detections if d.status == "known"]
        unknown_detections = [d for d in detections if d.status == "unknown"]

        return ImageAnalysisResult(
            image_id=image_id,
            filename=filename,
            image_index=image_index,
            width=w,
            height=h,
            original_url=f"/api/storage/uploads/{log_id}/{filename}",
            mask_url=f"/api/storage/outputs/{log_id}/{image_id}_mask.png",
            overlay_url=f"/api/storage/outputs/{log_id}/{image_id}_overlay.png",
            thumbnail_url=f"/api/storage/outputs/{log_id}/{image_id}_thumb.jpg",
            detections=detections,
            known_detections=known_detections,
            unknown_detections=unknown_detections,
            ssl_features=ssl_feats,
            processing_time_ms=proc_time,
            location_available=latitude is not None and longitude is not None,
            latitude=latitude,
            longitude=longitude,
            location_note=location_note,
            is_mock=True
        )
