import unittest

from app.schemas.detection import (
    BoundingBox,
    DetectionItem,
    ImageAnalysisResult,
    SSLFeatures,
    SegmentationArea,
)
from app.services.geolocation_service import geolocation_service
from app.services.log_service import LogService


class TestGeolocationService(unittest.TestCase):
    def setUp(self):
        self.csv = (
            b"image_id,filename,timestamp,latitude,longitude,heading,ping_number\n"
            b"frame-001,sss_001.png,2026-09-05T10:21:31.420Z,12.345678,80.123456,92.5,17\n"
            b"frame-002,sss_002.png,2026-09-05T10:21:32.420Z,12.345700,80.123500,93.0,18\n"
        )

    def test_loads_normalized_bay_metadata(self):
        records = geolocation_service.load_metadata(self.csv, "bay_of_bengal.csv")
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].latitude, 12.345678)
        self.assertEqual(records[0].longitude, 80.123456)
        self.assertEqual(records[0].heading, 92.5)

    def test_matches_id_before_filename_and_returns_null_when_missing(self):
        records = geolocation_service.load_metadata(self.csv)
        by_id = geolocation_service.match(records, "frame-001", "wrong.png")
        by_filename = geolocation_service.match(records, "other-id", "sss_002.png")
        missing = geolocation_service.match(records, "other-id", "missing.png")
        self.assertEqual(by_id.match_method, "image_id")
        self.assertEqual(by_filename.match_method, "filename")
        self.assertIsNone(missing)

    def test_timestamp_match_requires_tolerance(self):
        records = geolocation_service.load_metadata(self.csv)
        matched = geolocation_service.match(records, "unknown", "unknown.png", records[0].timestamp)
        rejected = geolocation_service.match(records, "unknown", "unknown.png", records[0].timestamp.replace(second=0))
        self.assertEqual(matched.match_method, "timestamp")
        self.assertIsNone(rejected)

    def test_detection_inherits_frame_location(self):
        service = LogService()
        detail = service.create_survey_from_files(
            "Geolocation Test",
            [("sss_001.png", b"not-an-image")],
            location_metadata=geolocation_service.load_metadata(self.csv),
        )
        detection = DetectionItem(
            object_id="known-1",
            class_name="shipwreck",
            status="known",
            confidence=0.9,
            bbox=BoundingBox(xmin=1, ymin=1, xmax=2, ymax=2),
            segmentation=SegmentationArea(pixel_count=1, contour_points=[[1, 1]]),
            is_mock=False,
        )
        result = ImageAnalysisResult(
            image_id=detail.images[0].image_id,
            filename="sss_001.png",
            image_index=1,
            width=8,
            height=8,
            original_url="/image.png",
            mask_url="/mask.png",
            overlay_url="/overlay.png",
            thumbnail_url="/thumb.jpg",
            detections=[detection],
            known_detections=[detection],
            unknown_detections=[],
            ssl_features=SSLFeatures(is_mock=False),
            processing_time_ms=1,
            is_mock=False,
        )
        service.update_image_result(detail.log_id, detail.images[0].image_id, result)
        updated = service.get_log_detail(detail.log_id)
        self.assertIsNotNone(updated.images[0].analysis_result.location)
        self.assertEqual(updated.images[0].analysis_result.detections[0].location.latitude, 12.345678)
        self.assertEqual(len(updated.track), 2)


if __name__ == "__main__":
    unittest.main()