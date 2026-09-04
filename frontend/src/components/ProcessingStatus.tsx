import React from 'react';
import { Loader2, CheckCircle2, Clock, Target, Cpu } from 'lucide-react';
import type { AnalysisStatusResponse, ImageRecord } from '../types/sonar';

interface ProcessingStatusProps {
  status: AnalysisStatusResponse;
  images: ImageRecord[];
  logName: string;
}

export const ProcessingStatus: React.FC<ProcessingStatusProps> = ({
  status,
  images,
  logName
}) => {
  const isCompleted = status.status === 'COMPLETED';

  return (
    <div className="space-y-6">
      {/* Top Banner Stats */}
      <div className="bg-sonar-900/80 rounded-xl border border-sonar-700/60 p-6 shadow-xl">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-sonar-700/60">
          <div>
            <span className="text-xs font-mono text-sonar-accent uppercase tracking-wider block">
              Side-Scan Sonar Analysis Pipeline
            </span>
            <h2 className="text-2xl font-bold font-mono text-white mt-1">
              {logName}
            </h2>
          </div>

          <div className="flex items-center space-x-3">
            <div className="bg-sonar-800 px-4 py-2 rounded-lg border border-sonar-700 flex items-center space-x-2">
              <Cpu className="w-4 h-4 text-sonar-cyan" />
              <span className="text-xs font-mono text-slate-300">
                Speed: <strong className="text-white">{status.processing_speed_fps || 2.4} img/sec</strong>
              </span>
            </div>

            {status.is_mock && (
              <span className="text-xs font-mono font-semibold bg-sonar-amber/20 text-sonar-amber px-3 py-2 rounded-lg border border-sonar-amber/30">
                DEMO INFERENCE PIPELINE
              </span>
            )}
          </div>
        </div>

        {/* Progress Bar & Percentage */}
        <div className="mt-6">
          <div className="flex justify-between items-center text-sm font-mono mb-2">
            <span className="text-slate-300">
              Processing Progress: <strong className="text-sonar-accent">{status.processed_images} / {status.total_images} images</strong>
            </span>
            <span className="text-xl font-bold text-white">
              {status.progress_percent}%
            </span>
          </div>

          <div className="w-full h-4 bg-sonar-950 rounded-full overflow-hidden p-0.5 border border-sonar-800">
            <div
              className="h-full bg-gradient-to-r from-sonar-cyan via-sonar-accent to-sonar-emerald rounded-full transition-all duration-300 shadow-lg shadow-sonar-accent/20"
              style={{ width: `${status.progress_percent}%` }}
            />
          </div>
        </div>

        {/* Realtime stats grid */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 mt-6">
          <div className="bg-sonar-950/60 p-3 rounded-lg border border-sonar-800">
            <span className="text-xs text-slate-400 font-mono block">Current Image</span>
            <span className="text-sm font-bold font-mono text-white truncate block">
              {status.current_image || (isCompleted ? 'Completed' : 'Initializing...')}
            </span>
          </div>

          <div className="bg-sonar-950/60 p-3 rounded-lg border border-sonar-800">
            <span className="text-xs text-slate-400 font-mono block">Objects Detected</span>
            <span className="text-sm font-bold font-mono text-sonar-accent block">
              {status.detections_count}
            </span>
          </div>

          <div className="bg-sonar-950/60 p-3 rounded-lg border border-sonar-800">
            <span className="text-xs text-slate-400 font-mono block">Known Shipwrecks</span>
            <span className="text-sm font-bold font-mono text-sonar-cyan block">
              {status.known_count}
            </span>
          </div>

          <div className="bg-sonar-950/60 p-3 rounded-lg border border-sonar-800">
            <span className="text-xs text-slate-400 font-mono block">Potential Unknown Objects</span>
            <span className="text-sm font-bold font-mono text-sonar-amber block">
              {status.unknown_count}
            </span>
          </div>

          <div className="bg-sonar-950/60 p-3 rounded-lg border border-sonar-800">
            <span className="text-xs text-slate-400 font-mono block">Avg Confidence</span>
            <span className="text-sm font-bold font-mono text-sonar-emerald block">
              {(status.average_confidence * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      {/* Live Image Pipeline Stream Checklist */}
      <div className="bg-sonar-900/80 rounded-xl border border-sonar-700/60 p-6 shadow-xl">
        <h3 className="text-sm font-semibold font-mono text-slate-200 uppercase tracking-wider mb-4">
          Live Frame Processing Checklist
        </h3>

        <div className="max-h-[380px] overflow-y-auto space-y-2 pr-2">
          {images.map((img, idx) => {
            const isDone = img.analysis_result !== null && img.analysis_result !== undefined;
            const isCurrent = !isDone && status.current_image === img.filename;

            return (
              <div
                key={img.image_id || idx}
                className={`p-3 rounded-lg border flex items-center justify-between text-sm font-mono transition-all ${
                  isDone
                    ? 'bg-sonar-800/40 border-sonar-emerald/30 text-slate-200'
                    : isCurrent
                    ? 'bg-sonar-cyan/10 border-sonar-cyan/50 text-white animate-pulse'
                    : 'bg-sonar-950/40 border-sonar-800/60 text-slate-500'
                }`}
              >
                <div className="flex items-center space-x-3">
                  {isDone ? (
                    <CheckCircle2 className="w-4 h-4 text-sonar-emerald flex-shrink-0" />
                  ) : isCurrent ? (
                    <Loader2 className="w-4 h-4 text-sonar-cyan animate-spin flex-shrink-0" />
                  ) : (
                    <Clock className="w-4 h-4 text-slate-600 flex-shrink-0" />
                  )}
                  <span className="w-8 text-xs text-slate-500">#{img.image_index}</span>
                  <span className="font-semibold">{img.filename}</span>
                </div>

                <div className="flex items-center space-x-4 text-xs">
                  {isDone ? (
                    <>
                      {img.analysis_result?.detections && img.analysis_result.detections.length > 0 ? (
                        <span className="flex items-center space-x-1 text-sonar-accent font-semibold">
                          <Target className="w-3.5 h-3.5" />
                          <span>{img.analysis_result.detections.length} Object(s)</span>
                        </span>
                      ) : (
                        <span className="text-slate-400">Normal Seabed</span>
                      )}
                      <span className="text-slate-400">
                        {img.analysis_result?.processing_time_ms} ms
                      </span>
                    </>
                  ) : isCurrent ? (
                    <span className="text-sonar-cyan font-semibold">Analyzing SSS frame...</span>
                  ) : (
                    <span className="text-slate-600">Pending</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
