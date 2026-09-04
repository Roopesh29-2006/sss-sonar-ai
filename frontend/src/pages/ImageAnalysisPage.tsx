import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, ArrowLeft, RefreshCw, AlertCircle } from 'lucide-react';
import { api } from '../services/api';
import type { ImageRecord, SurveyLogDetail } from '../types/sonar';
import { ImageOverlayViewer } from '../components/ImageOverlayViewer';
import { DetectionDetails } from '../components/DetectionDetails';
import { SSLFeatureViewer } from '../components/SSLFeatureViewer';

export const ImageAnalysisPage: React.FC = () => {
  const { logId, imageId } = useParams<{ logId: string; imageId: string }>();
  const navigate = useNavigate();

  const [surveyDetail, setSurveyDetail] = useState<SurveyLogDetail | null>(null);
  const [currentImage, setCurrentImage] = useState<ImageRecord | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!logId || !imageId) return;

    const loadData = async () => {
      try {
        setLoading(true);
        const detail = await api.getLogDetail(logId);
        setSurveyDetail(detail);

        const img = detail.images.find((i) => i.image_id === imageId);
        if (img) {
          setCurrentImage(img);
        } else {
          setError(`Image '${imageId}' not found in survey log.`);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load image analysis data.');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [logId, imageId]);

  if (loading) {
    return (
      <div className="p-16 text-center text-slate-300">
        <RefreshCw className="w-10 h-10 animate-spin mx-auto text-sonar-accent mb-3" />
        <p className="font-mono text-sm">Loading Sonar Image Frame...</p>
      </div>
    );
  }

  if (error || !currentImage || !surveyDetail) {
    return (
      <div className="max-w-xl mx-auto p-6 bg-sonar-rose/10 border border-sonar-rose/30 text-sonar-rose rounded-xl text-center">
        <AlertCircle className="w-10 h-10 mx-auto mb-2" />
        <p className="font-mono text-sm">{error || 'Image not found.'}</p>
        <button
          onClick={() => navigate(`/survey/${logId}`)}
          className="mt-4 px-4 py-2 bg-sonar-800 text-white rounded-lg font-mono text-xs"
        >
          Return to Survey Analysis
        </button>
      </div>
    );
  }

  // Navigation handlers
  const sortedImages = surveyDetail.images;
  const currentIndex = sortedImages.findIndex((i) => i.image_id === currentImage.image_id);
  const prevImage = currentIndex > 0 ? sortedImages[currentIndex - 1] : null;
  const nextImage = currentIndex < sortedImages.length - 1 ? sortedImages[currentIndex + 1] : null;

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-sonar-900/80 p-4 rounded-xl border border-sonar-700/60 shadow-xl">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => navigate(`/survey/${logId}`)}
            className="p-2 bg-sonar-800 hover:bg-sonar-700 text-slate-300 rounded-lg border border-sonar-700 transition-colors"
            title="Back to Survey Summary"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="text-[11px] font-mono text-sonar-accent uppercase tracking-wider">
              Frame {currentImage.image_index} / {surveyDetail.total_images}
            </div>
            <h1 className="text-xl font-bold font-mono text-white">
              {currentImage.filename}
            </h1>
          </div>
        </div>

        {/* Previous / Next Controls */}
        <div className="flex items-center space-x-2">
          <button
            disabled={!prevImage}
            onClick={() => prevImage && navigate(`/image/${logId}/${prevImage.image_id}`)}
            className="px-3 py-1.5 bg-sonar-800 hover:bg-sonar-700 disabled:opacity-40 text-white rounded-lg border border-sonar-700 text-xs font-mono flex items-center space-x-1 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Prev Frame</span>
          </button>

          <span className="text-xs font-mono text-slate-400 px-2">
            #{currentImage.image_index}
          </span>

          <button
            disabled={!nextImage}
            onClick={() => nextImage && navigate(`/image/${logId}/${nextImage.image_id}`)}
            className="px-3 py-1.5 bg-sonar-800 hover:bg-sonar-700 disabled:opacity-40 text-white rounded-lg border border-sonar-700 text-xs font-mono flex items-center space-x-1 transition-colors"
          >
            <span>Next Frame</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Grid: Image Overlay & Detection Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 columns: Image Overlay Viewer */}
        <div className="lg:col-span-2 space-y-6">
          <ImageOverlayViewer
            originalUrl={currentImage.original_url}
            overlayUrl={currentImage.analysis_result?.overlay_url}
            maskUrl={currentImage.analysis_result?.mask_url}
            result={currentImage.analysis_result}
            filename={currentImage.filename}
          />

          {/* SSL Feature Panel underneath viewer */}
          <SSLFeatureViewer sslFeatures={currentImage.analysis_result?.ssl_features} />
        </div>

        {/* Right column: Detection Details Panel */}
        <div>
          <DetectionDetails
            result={currentImage.analysis_result}
            filename={currentImage.filename}
            imageIndex={currentImage.image_index}
          />
        </div>
      </div>
    </div>
  );
};
