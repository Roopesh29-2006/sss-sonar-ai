import React from 'react';
import { Target, AlertTriangle, MapPin, Box } from 'lucide-react';
import type { ImageAnalysisResult } from '../types/sonar';

interface DetectionDetailsProps {
  result?: ImageAnalysisResult | null;
  filename: string;
  imageIndex: number;
}

export const DetectionDetails: React.FC<DetectionDetailsProps> = ({
  result,
  filename,
  imageIndex
}) => {
  const detections = result?.detections || [];
  const unknownDetections = detections.filter((det) => det.status === 'unknown' || det.class_name === 'unknown_object');

  return (
    <div className="bg-sonar-900/80 rounded-xl border border-sonar-700/60 p-4 shadow-xl flex flex-col h-full">
      <div className="flex items-center justify-between pb-3 border-b border-sonar-700/60 mb-3">
        <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
          <Target className="w-4 h-4 text-sonar-accent" />
          <span>Detection Results ({detections.length})</span>
        </h3>
        {result?.is_mock && (
          <span className="text-[10px] font-mono uppercase bg-sonar-amber/20 text-sonar-amber px-2 py-0.5 rounded border border-sonar-amber/30">
            DEMO VALUES ONLY
          </span>
        )}
      </div>

      {detections.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center p-6 text-center text-slate-400">
          <Box className="w-10 h-10 text-slate-600 mb-2" />
          <p className="text-sm font-medium">No objects detected</p>
          <p className="text-xs text-slate-500 mt-1">
            This Side-Scan Sonar frame contains normal seabed background.
          </p>
        </div>
      ) : (
        <div className="space-y-3 overflow-y-auto max-h-[460px] pr-1">
          {unknownDetections.length > 0 && (
            <div className="rounded-lg border border-sonar-amber/40 bg-sonar-amber/10 px-3 py-2 text-xs text-sonar-amber">
              <div className="font-semibold">Potential Unknown Objects ({unknownDetections.length})</div>
              <div className="mt-1 text-[11px] text-slate-300">Experimental object-discovery result — requires human verification.</div>
            </div>
          )}
          {detections.map((det, idx) => {
            const isUnknown = det.status === 'unknown' || det.class_name === 'unknown_object';
            const isShipwreck = !isUnknown;

            return (
              <div
                key={det.object_id || idx}
                className={`p-3.5 rounded-lg border backdrop-blur transition-all ${
                  isShipwreck
                    ? 'bg-sonar-800/60 border-sonar-accent/40 hover:border-sonar-accent'
                    : 'bg-sonar-800/60 border-sonar-amber/40 hover:border-sonar-amber'
                }`}
              >
                {/* Object Header */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-mono font-bold text-slate-300">
                      Object #{idx + 1}
                    </span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded font-semibold font-mono ${
                        isShipwreck
                          ? 'bg-sonar-accent/20 text-sonar-accent border border-sonar-accent/30'
                          : 'bg-sonar-amber/20 text-sonar-amber border border-sonar-amber/30'
                      }`}
                    >
                      {isShipwreck ? 'Known Shipwreck' : 'Potential Unknown Object'}
                    </span>
                  </div>
                  {isUnknown && (
                    <span className="flex items-center text-[11px] font-mono text-sonar-amber">
                      <AlertTriangle className="w-3 h-3 mr-1" /> Unknown
                    </span>
                  )}
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-2 gap-2 text-xs font-mono my-2.5">
                  {isShipwreck ? (
                    <div className="bg-sonar-950/60 p-2 rounded border border-sonar-800">
                      <span className="text-slate-400 block text-[10px] uppercase">Confidence</span>
                      <span className="text-sm font-bold text-white">
                        {det.confidence === null ? 'N/A' : `${(det.confidence * 100).toFixed(1)}%`}
                      </span>
                    </div>
                  ) : (
                    <div className="bg-sonar-950/60 p-2 rounded border border-sonar-800">
                      <span className="text-slate-400 block text-[10px] uppercase">Status</span>
                      <span className="text-sm font-bold text-sonar-amber">Unknown</span>
                    </div>
                  )}

                  <div className="bg-sonar-950/60 p-2 rounded border border-sonar-800">
                    <span className="text-slate-400 block text-[10px] uppercase">Novelty Score</span>
                    <span className={`text-sm font-bold ${isUnknown ? 'text-sonar-amber' : 'text-slate-500'}`}>
                      {det.novelty_score === null ? 'N/A' : det.novelty_score.toFixed(3)}
                    </span>
                  </div>
                </div>

                {/* Geometry details */}
                <div className="text-[11px] font-mono text-slate-400 space-y-1 bg-sonar-950/40 p-2 rounded border border-sonar-800/80">
                  <div className="flex justify-between">
                    <span>Bounding Box:</span>
                    <span className="text-slate-200">
                      [{Math.round(det.bbox.xmin)}, {Math.round(det.bbox.ymin)}, {Math.round(det.bbox.xmax)}, {Math.round(det.bbox.ymax)}]
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Segmentation Area:</span>
                    <span className="text-slate-200">{det.segmentation.pixel_count} px</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Frame/Image ID:</span>
                    <span className="text-slate-200">#{imageIndex} / {result?.image_id || filename}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Geolocation Section */}
      <div className="mt-4 pt-3 border-t border-sonar-700/60 text-xs font-mono text-slate-400 flex items-start space-x-2 bg-sonar-950/40 p-2.5 rounded border border-sonar-800">
        <MapPin className="w-4 h-4 text-slate-500 flex-shrink-0 mt-0.5" />
        <div>
          <span className="text-slate-300 font-semibold block">Location Status:</span>
          {result?.location ? (
            <div className="text-slate-300 space-y-0.5 mt-1">
              <div className="text-sonar-emerald">GPS Available</div>
              <div>Latitude: {result.location.latitude.toFixed(6)}</div>
              <div>Longitude: {result.location.longitude.toFixed(6)}</div>
              <div>Source: {result.location.source}</div>
              <div className="text-slate-500">Frame location, not exact object location</div>
            </div>
          ) : (
            <div className="text-slate-400 italic mt-1">
              <div>Location data unavailable</div>
              <div className="not-italic text-slate-500">No valid navigation metadata was found for this frame.</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
