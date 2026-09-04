export interface BoundingBox {
  xmin: number;
  ymin: number;
  xmax: number;
  ymax: number;
}

export interface SegmentationArea {
  pixel_count: number;
  contour_points: number[][];
}

export interface LocationInfo {
  latitude: number;
  longitude: number;
  source: string;
  timestamp?: string | null;
  match_method: string;
  match_error_seconds?: number | null;
  location_label: string;
}

export interface DetectionItem {
  object_id: string;
  class_name: 'shipwreck' | 'unknown_object' | string;
  status: 'known' | 'unknown' | string;
  confidence: number | null;
  novelty_score: number | null;
  bbox: BoundingBox;
  segmentation: SegmentationArea;
  location?: LocationInfo | null;
  is_mock: boolean;
}

export interface SSLFeatures {
  feature_vector: number[];
  similarity_score: number;
  novelty_score: number;
  is_mock: boolean;
}

export interface ImageAnalysisResult {
  image_id: string;
  filename: string;
  image_index: number;
  width: number;
  height: number;
  original_url: string;
  mask_url: string;
  overlay_url: string;
  thumbnail_url: string;
  detections: DetectionItem[];
  known_detections: DetectionItem[];
  unknown_detections: DetectionItem[];
  ssl_features: SSLFeatures;
  processing_time_ms: number;
  location_available: boolean;
  latitude?: number | null;
  longitude?: number | null;
  location_note: string;
  location?: LocationInfo | null;
  is_mock: boolean;
}

export interface ImageRecord {
  image_id: string;
  filename: string;
  image_index: number;
  file_path: string;
  original_url: string;
  upload_timestamp: string;
  file_size_bytes: number;
  latitude?: number | null;
  longitude?: number | null;
  location_note: string;
  location?: LocationInfo | null;
  analysis_result?: ImageAnalysisResult | null;
}

export interface SurveyLogSummary {
  log_id: string;
  log_name: string;
  total_images: number;
  upload_timestamp: string;
  status: 'UPLOADED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  processed_images: number;
  total_detections: number;
  known_count: number;
  unknown_count: number;
  images_with_known_detections: number;
  images_with_unknown_objects: number;
  high_confidence_count: number;
  average_confidence: number;
}

export interface SurveyLogDetail extends SurveyLogSummary {
  images: ImageRecord[];
  error_message?: string | null;
}

export interface AnalysisStatusResponse {
  log_id: string;
  status: 'UPLOADED' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  total_images: number;
  processed_images: number;
  progress_percent: number;
  current_image?: string | null;
  processing_speed_fps: number;
  detections_count: number;
  known_count: number;
  unknown_count: number;
  images_with_known_detections: number;
  images_with_unknown_objects: number;
  average_confidence: number;
  recent_logs: string[];
  error_message?: string | null;
  is_mock: boolean;
}

export interface DetectionsPerImage {
  image_id: string;
  filename: string;
  image_index: number;
  detections_count: number;
  known_count: number;
  unknown_count: number;
}

export interface SurveyResultsResponse {
  log_id: string;
  log_name: string;
  status: string;
  total_images: number;
  processed_images: number;
  total_detections: number;
  known_count: number;
  unknown_count: number;
  images_with_known_detections: number;
  images_with_unknown_objects: number;
  high_confidence_count: number;
  average_confidence: number;
  detections_per_image: DetectionsPerImage[];
  all_detections: DetectionItem[];
  location_available: boolean;
  track: TrackPoint[];
  is_mock: boolean;
}

export interface TrackPoint {
  latitude: number;
  longitude: number;
  timestamp?: string | null;
  source: string;
}

export interface HealthCheckResponse {
  status: string;
  system: string;
  version: string;
  inference_provider: string;
  is_mock: boolean;
  weights_ready: boolean;
}
