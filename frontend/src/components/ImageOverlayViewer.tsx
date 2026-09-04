import React, { useState } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, Eye, Layers, Columns } from 'lucide-react';
import { api } from '../services/api';
import type { ImageAnalysisResult } from '../types/sonar';

interface ImageOverlayViewerProps {
  originalUrl: string;
  maskUrl?: string;
  overlayUrl?: string;
  result?: ImageAnalysisResult | null;
  filename: string;
}

export const ImageOverlayViewer: React.FC<ImageOverlayViewerProps> = ({
  originalUrl,
  overlayUrl,
  result,
  filename
}) => {
  const [viewMode, setViewMode] = useState<'side-by-side' | 'overlay' | 'original'>('side-by-side');
  const [zoom, setZoom] = useState<number>(1);

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.25, 3));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.25, 0.75));
  const handleResetZoom = () => setZoom(1);

  const fullOriginalUrl = api.getAssetUrl(originalUrl);
  const fullOverlayUrl = overlayUrl ? api.getAssetUrl(overlayUrl) : fullOriginalUrl;

  return (
    <div className="bg-sonar-900/80 rounded-xl border border-sonar-700/60 p-4 shadow-xl">
      {/* Controls Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-sonar-700/60 mb-4">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono text-slate-400">View Mode:</span>
          <div className="bg-sonar-800 p-1 rounded-lg flex items-center space-x-1 border border-sonar-700">
            <button
              onClick={() => setViewMode('side-by-side')}
              className={`px-2.5 py-1 rounded text-xs font-medium flex items-center space-x-1 transition-colors ${
                viewMode === 'side-by-side'
                  ? 'bg-sonar-accent text-sonar-950 font-semibold'
                  : 'text-slate-300 hover:text-white'
              }`}
            >
              <Columns className="w-3.5 h-3.5" />
              <span>Side-by-Side</span>
            </button>
            <button
              onClick={() => setViewMode('overlay')}
              className={`px-2.5 py-1 rounded text-xs font-medium flex items-center space-x-1 transition-colors ${
                viewMode === 'overlay'
                  ? 'bg-sonar-accent text-sonar-950 font-semibold'
                  : 'text-slate-300 hover:text-white'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>AI Overlay</span>
            </button>
            <button
              onClick={() => setViewMode('original')}
              className={`px-2.5 py-1 rounded text-xs font-medium flex items-center space-x-1 transition-colors ${
                viewMode === 'original'
                  ? 'bg-sonar-accent text-sonar-950 font-semibold'
                  : 'text-slate-300 hover:text-white'
              }`}
            >
              <Eye className="w-3.5 h-3.5" />
              <span>Original SSS</span>
            </button>
          </div>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono text-slate-400 mr-1">Zoom: {Math.round(zoom * 100)}%</span>
          <button
            onClick={handleZoomOut}
            className="p-1.5 bg-sonar-800 hover:bg-sonar-700 text-slate-200 rounded border border-sonar-700"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={handleZoomIn}
            className="p-1.5 bg-sonar-800 hover:bg-sonar-700 text-slate-200 rounded border border-sonar-700"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={handleResetZoom}
            className="p-1.5 bg-sonar-800 hover:bg-sonar-700 text-slate-200 rounded border border-sonar-700"
            title="Reset Zoom"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Image View Container */}
      <div className="overflow-auto max-h-[560px] flex justify-center items-center p-2 bg-sonar-950/80 rounded-lg border border-sonar-800">
        <div
          style={{ transform: `scale(${zoom})`, transformOrigin: 'top center' }}
          className="transition-transform duration-150 w-full"
        >
          {viewMode === 'side-by-side' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex flex-col items-center">
                <div className="w-full text-center bg-sonar-800/80 text-xs font-mono py-1 rounded-t border border-sonar-700 text-slate-300">
                  Original SSS Sonar ({filename})
                </div>
                <img
                  src={fullOriginalUrl}
                  alt="Original Sonar"
                  className="w-full h-auto object-contain border border-sonar-700 rounded-b max-h-[440px]"
                />
              </div>

              <div className="flex flex-col items-center">
                <div className="w-full text-center bg-sonar-800/80 text-xs font-mono py-1 rounded-t border border-sonar-700 text-sonar-accent flex items-center justify-center space-x-2">
                  <span>AI Segmentation Overlay</span>
                  {result?.is_mock && (
                    <span className="bg-sonar-amber/20 text-sonar-amber text-[9px] px-1.5 py-0.2 rounded border border-sonar-amber/30">
                      DEMO
                    </span>
                  )}
                </div>
                <img
                  src={fullOverlayUrl}
                  alt="Detection Overlay"
                  className="w-full h-auto object-contain border border-sonar-700 rounded-b max-h-[440px]"
                />
              </div>
            </div>
          ) : viewMode === 'overlay' ? (
            <div className="flex flex-col items-center max-w-3xl mx-auto">
              <div className="w-full text-center bg-sonar-800/80 text-xs font-mono py-1 rounded-t border border-sonar-700 text-sonar-accent flex items-center justify-center space-x-2">
                <span>AI Detection Overlay</span>
                {result?.is_mock && (
                  <span className="bg-sonar-amber/20 text-sonar-amber text-[9px] px-1.5 py-0.2 rounded border border-sonar-amber/30">
                    DEMO MOCK
                  </span>
                )}
              </div>
              <img
                src={fullOverlayUrl}
                alt="Detection Overlay"
                className="w-full h-auto object-contain border border-sonar-700 rounded-b max-h-[500px]"
              />
            </div>
          ) : (
            <div className="flex flex-col items-center max-w-3xl mx-auto">
              <div className="w-full text-center bg-sonar-800/80 text-xs font-mono py-1 rounded-t border border-sonar-700 text-slate-300">
                Original SSS Image ({filename})
              </div>
              <img
                src={fullOriginalUrl}
                alt="Original Sonar"
                className="w-full h-auto object-contain border border-sonar-700 rounded-b max-h-[500px]"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
